import { api } from "./api";

// Phone cameras produce 3-8 MB photos. Shrinking them in the browser before the
// request keeps the upload quick on Wi-Fi and saves the reverse proxy a long
// transfer; the backend still normalises the JPEG before storing it.
const MAX_SIDE = 2400;
const QUALITY = 0.88;
const ALREADY_SMALL = 900 * 1024;

function loadImage(file: File): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const image = new Image();
    image.onload = () => {
      URL.revokeObjectURL(url);
      resolve(image);
    };
    image.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error("unreadable image"));
    };
    image.src = url;
  });
}

async function decode(file: File): Promise<ImageBitmap | HTMLImageElement> {
  if (typeof createImageBitmap === "function") {
    try {
      return await createImageBitmap(file, { imageOrientation: "from-image" });
    } catch {
      // Unsupported format or old browser: fall back to an <img> element.
    }
  }
  return loadImage(file);
}

function toBlob(canvas: HTMLCanvasElement): Promise<Blob | null> {
  return new Promise((resolve) => canvas.toBlob(resolve, "image/jpeg", QUALITY));
}

/** Re-encodes a camera photo to a smaller JPEG, keeping the EXIF orientation. */
export async function preparePhoto(file: File): Promise<Blob> {
  if (!file.type.startsWith("image/")) return file;
  let source: ImageBitmap | HTMLImageElement;
  try {
    source = await decode(file);
  } catch {
    return file;
  }
  try {
    const width = source.width;
    const height = source.height;
    const scale = Math.min(1, MAX_SIDE / Math.max(width, height));
    if (scale === 1 && file.size <= ALREADY_SMALL) return file;
    const canvas = document.createElement("canvas");
    canvas.width = Math.max(1, Math.round(width * scale));
    canvas.height = Math.max(1, Math.round(height * scale));
    const context = canvas.getContext("2d");
    if (!context) return file;
    context.fillStyle = "#fff";
    context.fillRect(0, 0, canvas.width, canvas.height);
    context.drawImage(source, 0, 0, canvas.width, canvas.height);
    const blob = await toBlob(canvas);
    return blob && blob.size > 0 && blob.size < file.size ? blob : file;
  } catch {
    return file;
  } finally {
    if (typeof ImageBitmap !== "undefined" && source instanceof ImageBitmap)
      source.close();
  }
}

/** Uploads a photo, preparing it in the browser first, and returns its name. */
export async function uploadPhoto(file: File): Promise<string> {
  const prepared = await preparePhoto(file);
  const form = new FormData();
  form.append(
    "file",
    prepared,
    prepared instanceof File ? prepared.name : "photo.jpg",
  );
  const uploaded = await api<{ path: string }>("photos", {
    method: "POST",
    body: form,
  });
  return uploaded.path;
}
