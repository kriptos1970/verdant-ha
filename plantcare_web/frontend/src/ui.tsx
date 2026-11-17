import {adaptiveIcon} from "./ios-icons";
import React, { useState, useEffect, useRef } from "react";
import {
  Leaf,
  X,
  Droplets,
  FlaskConical,
  RotateCw,
  ShieldCheck,
  Sprout,
  Scissors,
  Package,
  TrendingUp,
  MapPin,
} from "lucide-react";
import type { Plant, Product, Action } from "./types";
import { photoURL } from "./api";
import { useI18n } from "./i18n";
const careIcons = {
 water: adaptiveIcon('water', Droplets),
 feed: adaptiveIcon('sparkles', FlaskConical),
 rotate: adaptiveIcon('rotate', RotateCw),
 health: adaptiveIcon('health', ShieldCheck),
 prune: adaptiveIcon('scissors',Scissors),
 repot: adaptiveIcon('box',Package),
 progress: adaptiveIcon('chart',TrendingUp),
 treatment: adaptiveIcon('flask',FlaskConical),
 move: adaptiveIcon('pin',MapPin),
 other: adaptiveIcon('leaf', Sprout),
};
export const eventIcon = (kind: string) => kind === 'Annaffia' ? careIcons.water : kind === 'Concima' ? careIcons.feed : kind === 'Ruota' ? careIcons.rotate : kind === 'Controlla salute' ? careIcons.health : kind === 'Pota' ? careIcons.prune : kind === 'Rinvasa' ? careIcons.repot : kind === 'Aggiorna progressi' ? careIcons.progress : kind === 'Trattamento' ? careIcons.treatment : kind === 'Spostamento' ? careIcons.move : careIcons.other;

export function Avatar({
  plant,
  large = false,
}: {
  plant: Plant;
  large?: boolean;
}) {
  const [failed, setFailed] = useState(false);
  const src =
    photoURL(plant.photoPath, !large) ||
    (/^https:\/\//.test(plant.catalogImageURL || "")
      ? plant.catalogImageURL
      : undefined);
  useEffect(() => setFailed(false), [src]);
  return src && !failed ? (
    <img
      className={large ? "plant-cover" : "avatar"}
      src={src}
      alt={large ? plant.name : ""}
      loading="lazy"
      onError={() => setFailed(true)}
    />
  ) : (
    <div className={large ? "plant-cover placeholder" : "avatar placeholder"}>
      <Leaf size={large ? 70 : 24} />
    </div>
  );
}
export function ProductPhoto({product}:{product:Product}) {
  const [failed,setFailed]=useState(false);
  const src=photoURL(product.photoPath);
  useEffect(()=>setFailed(false),[src]);
  return src&&!failed ? <a className="product-photo" href={src} target="_blank" rel="noreferrer" aria-label={`Apri foto di ${product.name}`}><img src={photoURL(product.photoPath,true)} alt={`Foto di ${product.name}`} loading="lazy" onError={()=>setFailed(true)}/></a> : <div className="product-icon"><FlaskConical size={28}/></div>;
}

export function Modal({
  title,
  onClose,
  children,
}: {
  title: string;
  onClose: () => void;
  children: React.ReactNode;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const { t } = useI18n();
  useEffect(() => {
    const d = ref.current;
    d?.showModal();
    return () => {
      d?.close();
    };
  }, []);
  return (
    <dialog
      ref={ref}
      onCancel={(e) => {
        e.preventDefault();
        onClose();
      }}
      onClick={(e) => {
        if (e.target === ref.current) onClose();
      }}
    >
      <div className="modal-top">
        <h2>{title}</h2>
        <button className="icon-button" aria-label={t("common.close")} onClick={onClose}>
          <X size={21} />
        </button>
      </div>
      {children}
    </dialog>
  );
}

export const actionLabel = (a: Action) =>
  a.includesFertilizing
    ? "Annaffiatura + concimazione"
    : a.kind === "Aggiorna progressi"
      ? "Diario di crescita"
      : a.kind;
