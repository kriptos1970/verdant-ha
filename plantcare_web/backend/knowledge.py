"""Native Pl@ntNet recognition and Perenual reference profiles, without sync."""
import io
import math
import re
import warnings
import httpx
from PIL import Image, ImageOps, UnidentifiedImageError
from .domain import iso, now, swift_round

ORGANS = {'leaf', 'flower', 'fruit', 'bark', 'auto'}


def key(settings, service):
    value = settings.options.get(service + '_api_key', '').strip()
    if not value:
        raise ValueError(f'Configura la chiave {"Pl@ntNet" if service == "plantnet" else "Perenual"} nelle opzioni dell’add-on Home Assistant e riavvia PlantCare.')
    return value


def normalized_jpeg(content):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(content)) as original:
                if original.format not in {'JPEG', 'PNG', 'WEBP'}:
                    raise ValueError('Usa una fotografia JPEG, PNG o WebP.')
                image = ImageOps.exif_transpose(original)
                image.thumbnail((2000, 2000), Image.Resampling.LANCZOS)
                output = io.BytesIO()
                image.convert('RGB').save(output, 'JPEG', quality=86)
                return output.getvalue()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise ValueError('Immagine non leggibile o troppo grande. Usa JPEG, PNG o WebP.') from None


def category(scientific, family):
    value = (scientific + ' ' + family).lower()
    for tokens, result in [(('cact', 'aloe', 'echeveria'), 'Succulenta'), (('ocimum', 'mentha', 'rosmar'), 'Aromatica'), (('orchid', 'rosa'), 'Fiorita')]:
        if any(t in value for t in tokens):
            return result
    return 'Tropicale'


def text(value, limit=300):
    return value[:limit] if isinstance(value, str) else ''


def strings(value):
    return [text(v) for v in value[:30] if isinstance(v, str)] if isinstance(value, list) else []


async def identify(settings, content, organ):
    api_key = key(settings, 'plantnet')
    if organ not in ORGANS:
        raise ValueError('Parte della pianta non valida.')
    jpeg = normalized_jpeg(content)
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post('https://my-api.plantnet.org/v2/identify/all', params={'lang': 'it', 'include-related-images': 'true', 'api-key': api_key}, data={'organs': organ}, files={'images': ('verdant-plant.jpg', jpeg, 'image/jpeg')})
        if response.status_code == 404:
            return {'candidates': [], 'provider': 'Pl@ntNet'}
        response.raise_for_status()
    try:
        results = response.json()['results']
        if not isinstance(results, list): raise ValueError()
        candidates = []
        for result in results[:5]:
            species = result['species']
            scientific = text(species['scientificNameWithoutAuthor'])
            score = result['score']
            if not scientific or isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(score) or not 0 <= score <= 1: raise ValueError()
            common = strings(species.get('commonNames'))
            family = text((species.get('family') or {}).get('scientificNameWithoutAuthor'))
            candidates.append(dict(scientificName=scientific, commonName=common[0] if common else scientific, family=family, score=score, category=category(scientific, family)))
        return {'candidates': candidates, 'provider': 'Pl@ntNet'}
    except (ValueError, KeyError, TypeError, AttributeError):
        raise ValueError('Pl@ntNet ha restituito un risultato non utilizzabile. Riprova.') from None


def watering_days(benchmark, label):
    baseline = {'frequent': 3, 'average': 7, 'minimum': 14, 'none': 30}.get(str(label).lower(), 7)
    if isinstance(benchmark, dict) and 'day' in str(benchmark.get('unit', '')).lower():
        values = [int(v) for v in re.findall(r'\d{1,6}', str(benchmark.get('value', '')))]
        if values: return max(1, min(60, max(swift_round(sum(values) / len(values)), baseline)))
    return baseline


async def profile(settings, scientific):
    api_key = key(settings, 'perenual')
    scientific = scientific.strip()
    if not scientific or len(scientific) > 300: raise ValueError('Inserisci il nome scientifico della specie.')
    async with httpx.AsyncClient(timeout=30) as client:
        async def search(query):
            r = await client.get('https://www.perenual.com/api/v2/species-list', params={'key': api_key, 'q': query})
            r.raise_for_status()
            data = r.json().get('data')
            if not isinstance(data, list): raise ValueError('Risposta Perenual non utilizzabile.')
            return data
        try:
            items = await search(scientific)
            if not items and scientific.lower().startswith('goeppertia '):
                items = await search('Calathea ' + scientific.split(' ', 1)[1])
            if not items: return None
            match = next((i for i in items if scientific.casefold() in [v.casefold() for v in strings(i.get('scientific_name'))]), items[0])
            identifier = match['id']
            if type(identifier) is not int or identifier < 1: raise ValueError()
            r = await client.get(f'https://www.perenual.com/api/v2/species/details/{identifier}', params={'key': api_key})
            brief = r.status_code in (403, 429)
            if not brief: r.raise_for_status()
            data = match if brief else r.json()
            names = strings(data.get('scientific_name')) or strings(match.get('scientific_name'))
            if not names: raise ValueError()
            boolean = lambda k: data.get(k) if type(data.get(k)) is bool and not brief else None
            return dict(speciesID=identifier, scientificName=names[0], exactMatch=scientific.casefold() in [n.casefold() for n in names], wateringDays=watering_days(data.get('watering_general_benchmark'), data.get('watering')), wateringLabel=text(data.get('watering')), sunlight=strings(data.get('sunlight')), soil=strings(data.get('soil')), careLevel=text(data.get('care_level')), summary='Perenual ha fornito la scheda sintetica; i dettagli estesi non sono inclusi nel piano API corrente.' if brief else text(data.get('description'), 10000), source='Perenual · scheda sintetica' if brief else 'Perenual', sourceURL=f'https://perenual.com/plant-species-database-search-finder/species/{identifier}', fetchedAt=iso(now()), poisonousToHumans=boolean('poisonous_to_humans'), poisonousToPets=boolean('poisonous_to_pets'))
        except (KeyError, TypeError, AttributeError):
            raise ValueError('Perenual ha restituito una scheda non utilizzabile.') from None
