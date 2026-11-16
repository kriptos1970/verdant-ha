"""Port of AdaptiveCarePlanner.swift. Weather is explicit; no invented live climate."""
from copy import deepcopy
from uuid import uuid4
from zoneinfo import ZoneInfo
import httpx
from .domain import iso, now, parse, swift_round, feed_days, learning, evidence

PLACEMENTS = ['Balcone riparato', 'Pieno sole', 'Ombra', 'Mezza ombra · balcone', 'Patio', 'Pianerottolo', 'Interno luminoso', 'Interno poco luminoso']
OUTDOOR = set(PLACEMENTS[:5])
FACTORS = ['Posizione', 'Temperatura', 'Umidità', 'Pioggia', 'Stagione', 'Sicurezza', 'Allineamento']

def make_plan(species, family, placement, location, climate, at=None, zone='Europe/Rome', botanical=None):
    at = at or now()
    lower, fam = species.lower(), family.lower()
    succulent = any(t in fam for t in ['cactaceae', 'crassulaceae', 'aizoaceae']) or any(t in lower for t in ['aloe', 'echeveria', 'haworthia', 'crassula', 'sedum', 'sempervivum', 'kalanchoe', 'agave', 'lithops', 'gasteria', 'aeonium', 'pachyphytum', 'graptopetalum', 'portulacaria', 'sansevieria'])
    water, feed, reasons = 7., 28 if succulent else 21, []
    if botanical:
        water = max(botanical['wateringDays'], 21) if succulent else botanical['wateringDays']
        reasons.append(f"Scheda {botanical['source']}: irrigazione {botanical.get('wateringLabel', 'dalla scheda salvata')}, base ogni {botanical['wateringDays']} giorni.")
        for key, label in [('sunlight', 'Luce consigliata dalla scheda'), ('soil', 'Terreno consigliato')]:
            if botanical.get(key): reasons.append(f"{label}: {', '.join(botanical[key])}.")
    elif 'zamioculcas' in lower:
        water, feed = 18., 42
        reasons.append('La Zamioculcas immagazzina acqua nei rizomi e teme i ristagni.')
    elif 'dracaena' in lower:
        water, feed = 15., 30
        reasons.append('Questa specie tollera bene periodi asciutti.')
    elif succulent:
        water = 21.
        reasons.append('Le succulente richiedono terreno completamente asciutto tra le bagnature.')
    elif 'araceae' in fam:
        reasons.append('Le Araceae preferiscono umidità moderata ma non terreno saturo.')
    elif 'orchidaceae' in fam:
        water, feed = 8., 28
        reasons.append('Le orchidee richiedono drenaggio rapido e concime molto diluito.')
    elif 'pteridaceae' in fam or 'fern' in lower:
        water = 4.
        reasons.append('Le felci soffrono quando il substrato rimane asciutto a lungo.')
    standard_water, standard_feed = swift_round(water), feed
    placement_factor, reason = {
        'Pieno sole': (.75, 'Il pieno sole aumenta evaporazione e traspirazione.'),
        'Mezza ombra · balcone': (1.25 if succulent else .90, 'In mezza ombra una succulenta asciuga lentamente: attendi il substrato completamente secco.' if succulent else 'La mezza ombra esterna mantiene un consumo d’acqua medio.'),
        'Balcone riparato': (.85, 'Aria e vento del balcone asciugano più rapidamente il vaso.'),
        'Patio': (.95, 'Il patio offre una protezione parziale dal sole e dal vento.'),
        'Ombra': (1.55 if succulent else 1.15, 'In ombra il substrato asciuga più lentamente.'),
        'Pianerottolo': (1.10, 'Sul pianerottolo luce e ricambio d’aria sono generalmente ridotti.'),
        'Interno luminoso': (1., 'L’interno luminoso mantiene una crescita abbastanza regolare.'),
        'Interno poco luminoso': (1.55 if succulent else 1.15, 'Con poca luce la pianta usa meno acqua.'),
    }[placement]
    reasons.append(reason)
    multipliers = []
    temp, humidity, rain = (climate[k] for k in ['averageTemperature', 'relativeHumidity', 'precipitationNextWeek'])
    if temp >= 30: multipliers.append(('Temperatura', .80, 'Temperature medie molto alte accorciano l’intervallo.'))
    elif temp >= 25: multipliers.append(('Temperatura', .90, 'Il caldo previsto aumenta il fabbisogno d’acqua.'))
    elif temp < 12: multipliers.append(('Temperatura', 1.25, 'Con il freddo la crescita rallenta sensibilmente.'))
    if humidity < 40: multipliers.append(('Umidità', .95, 'L’aria secca accelera la perdita d’acqua.'))
    elif humidity > 75: multipliers.append(('Umidità', 1.10, 'L’umidità elevata rallenta l’asciugatura.'))
    if placement in OUTDOOR and rain > 15: multipliers.append(('Pioggia', 1.15, 'È prevista pioggia: evita di annaffiare se il vaso la riceve.'))
    climate_factor = 1.
    for _, multiplier, explanation in multipliers:
        climate_factor *= multiplier
        reasons.append(explanation)
    month, northern = at.astimezone(ZoneInfo(zone)).month, location['latitude'] >= 0
    if month in ([5,6,7,8,9] if northern else [11,12,1,2,3]):
        season, season_factor = 'Crescita attiva', .95
        reasons.append('Il periodo vegetativo richiede controlli più frequenti.')
    elif month in ([11,12,1,2] if northern else [5,6,7,8]):
        season, season_factor, feed = 'Riposo vegetativo', 1.20, feed * 2
        reasons.append('Nel riposo vegetativo acqua e fertilizzante vanno ridotti.')
    else:
        season, season_factor = 'Transizione stagionale', 1.
        reasons.append('In questa fase osserva la nuova crescita prima di concimare.')
    calculated = swift_round(water * placement_factor * climate_factor * season_factor)
    minimum = {'Pieno sole':12, 'Balcone riparato':14, 'Interno luminoso':18, 'Mezza ombra · balcone':24, 'Patio':24, 'Ombra':30, 'Pianerottolo':30, 'Interno poco luminoso':30}[placement]
    water_days = max(minimum, min(60, calculated)) if succulent else max(2, min(35, calculated))
    if succulent: reasons.append(f'Soglia anti-marciume: almeno {minimum} giorni per questa esposizione, verificando sempre che il terriccio sia asciutto in profondità.')
    fertilizer = feed_days(feed, water_days)
    reasons.append(f'Concimazione allineata all’irrigazione: ogni {fertilizer} giorni (multiplo di {water_days}).')
    adjustments, running = [], water
    def adjustment(id, domain, factor, before, after, explanation):
        if before != after:
            adjustments.append(dict(id=id, domain=domain, factor=factor, baselineDays=before, deltaDays=after-before, resultingDays=after, explanation=explanation, source='Verdant'))
    factors = [('water.placement', 'Posizione', placement_factor, f'La posizione {placement.lower()} modifica la velocità con cui il vaso asciuga.')]
    factors += [('water.'+factor.lower(),factor,multiplier,explanation) for factor,multiplier,explanation in multipliers]
    factors += [('water.season','Stagione',season_factor, 'Nel riposo vegetativo il consumo d’acqua diminuisce.' if season_factor==1.20 else 'Durante la crescita attiva la pianta richiede controlli più frequenti.' if season_factor==.95 else 'La stagione di transizione non modifica l’intervallo standard.')]
    for id, factor, multiplier, explanation in factors:
        before = swift_round(running)
        running *= multiplier
        adjustment(id,'water',factor,before,swift_round(running),explanation)
    adjustment('water.safety','water','Sicurezza',swift_round(running),water_days,'Applicata la soglia anti-marciume prevista per questa esposizione.' if succulent else 'Applicati i limiti di sicurezza del piano Verdant.')
    adjustment('nutrition.season','nutrition','Stagione',standard_feed,feed,'Nel riposo vegetativo la concimazione viene diradata.')
    adjustment('nutrition.alignment','nutrition','Allineamento',feed,fertilizer,'La concimazione viene sincronizzata con un ciclo completo di annaffiatura.')
    parts = [str(location.get(k,'')).strip(' ,\t\n\r') for k in ['name','detail']]
    name = ', '.join(p for p in parts if p) if not parts[1] or parts[1].lower() not in parts[0].lower() else parts[0]
    return dict(placement=placement, locationName=name or 'Località non indicata', latitude=location['latitude'], longitude=location['longitude'], **climate, seasonName=season, wateringDays=water_days, fertilizingDays=fertilizer, inspectionDays=5 if placement in OUTDOOR else 7, generatedAt=iso(at), rationale=reasons, botanicalWateringDays=botanical['wateringDays'] if botanical else None, botanicalSource=botanical['source'] if botanical else None, botanicalSummary=botanical.get('summary') if botanical else None, verdantWateringDays=water_days, verdantFertilizingDays=fertilizer, revisionSource='Verdant', revisedAt=None, wateringAdjustmentDays=None, careLearning=None, standardWateringDays=standard_water, standardFertilizingDays=standard_feed, adjustments=adjustments, climateRevisionHistory=None)


def apply_plan(plant, plan, zone, previous=None, at=None):
    """Native refresh semantics: preserve manual/AI intervals, learn only otherwise."""
    at = at or now()
    plan = deepcopy(plan)
    preserve = previous and (plant.get('carePlanMode') == 'AI' or previous.get('revisionSource') == 'Modifica manuale' or (previous.get('revisionSource') == 'AI' and evidence(previous.get('revisionChangedIntervals'), previous.get('revisionReason') or '')))
    if preserve:
        plan.update(wateringDays=plant['wateringInterval'], fertilizingDays=plant.get('fertilizingInterval') or plan['fertilizingDays'], inspectionDays=plant.get('inspectionInterval') or plan['inspectionDays'])
        for key in ['revisionSource','revisedAt','revisionProvider','revisionReason','revisionChangedIntervals']: plan[key] = previous.get(key)
    else:
        summary = learning(plant, plan['verdantWateringDays'], zone)
        if summary:
            summary['updatedAt'] = iso(at)
            plan.update(wateringDays=summary['learnedIntervalDays'],careLearning=summary,revisionSource='Apprendimento dalle cure',revisedAt=iso(at))
        plan['fertilizingDays'] = feed_days(plan['verdantFertilizingDays'],plan['wateringDays'])
    if previous:
        if plan.get('botanicalSource')==previous.get('botanicalSource') and plan.get('botanicalWateringDays')==previous.get('botanicalWateringDays'):
            for key in ['botanicalScientificName','botanicalFetchedAt','botanicalExactMatch']:
                if key not in plan and key in previous:plan[key]=previous[key]
        history = deepcopy(previous.get('climateRevisionHistory') or [])
        if any(previous.get(k) != plan.get(k) for k in ['wateringDays','fertilizingDays','seasonName']):
            climate_keys = ['averageTemperature','relativeHumidity','precipitationNextWeek','seasonName']
            reasons = [a['explanation'] for a in plan['adjustments'] if a['factor'] in FACTORS[1:]]
            history.append(dict(id=str(uuid4()).upper(),date=iso(at),previousWateringDays=previous['wateringDays'],newWateringDays=plan['wateringDays'],previousFertilizingDays=previous['fertilizingDays'],newFertilizingDays=plan['fertilizingDays'],previousClimate={k:previous.get(k) for k in climate_keys},currentClimate={k:plan[k] for k in climate_keys},reasons=reasons or ['Il ricalcolo stagionale o climatico ha aggiornato il piano.']))
        plan['climateRevisionHistory'] = history[-12:]
    plant.update(adaptivePlan=plan,wateringInterval=plan['wateringDays'],fertilizingInterval=plan['fertilizingDays'])
    if plant.get('inspectionInterval') is not None: plant['inspectionInterval'] = plan['inspectionDays']
    return plant


def saved_botanical(previous):
    if not previous.get('botanicalWateringDays'): return None
    return dict(wateringDays=previous['botanicalWateringDays'],wateringLabel='dalla scheda salvata',source=previous.get('botanicalSource') or 'Perenual',summary=previous.get('botanicalSummary'))


async def fetch_climate(location):
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get('https://api.open-meteo.com/v1/forecast',params=dict(latitude=location['latitude'],longitude=location['longitude'],current='temperature_2m,relative_humidity_2m',daily='temperature_2m_max,temperature_2m_min,precipitation_sum',forecast_days=7,timezone='auto'))
        response.raise_for_status()
    data = response.json()
    means = [(a+b)/2 for a,b in zip(data['daily']['temperature_2m_max'],data['daily']['temperature_2m_min'])]
    from .models import ClimateInput
    return ClimateInput(averageTemperature=sum(means)/len(means) if means else data['current']['temperature_2m'],relativeHumidity=data['current']['relative_humidity_2m'],precipitationNextWeek=sum(data['daily']['precipitation_sum'])).model_dump()


async def refresh_all(store, settings, force=False):
    """Fetch outside transactions, then recheck version to avoid overwriting user edits."""
    at, cache, updated, errors = now(), {}, 0, 0
    for plant, version in store.list('plants'):
        previous = plant.get('adaptivePlan')
        if plant.get('carePlanMode') not in ['Intelligente','AI'] or not previous or not previous.get('weatherEnabled'): continue
        if not force and parse(previous['generatedAt']).astimezone(ZoneInfo(settings.zone)).date() >= at.astimezone(ZoneInfo(settings.zone)).date(): continue
        try:
            location = dict(name=previous['locationName'],detail='',latitude=previous['latitude'],longitude=previous['longitude'])
            key = (location['latitude'],location['longitude'])
            if key not in cache: cache[key] = await fetch_climate(location)
            plan = make_plan(plant['species'],plant.get('family') or '',previous['placement'],location,cache[key],at,settings.zone,saved_botanical(previous))
            plan['weatherEnabled'] = True
            apply_plan(plant,plan,settings.zone,previous,at)
            with store.connection() as db:
                store.put('plants',plant,version,db)
            updated += 1
        except Exception:
            errors += 1
    result = dict(lastRun=iso(at),updated=updated,errors=errors)
    store.set_state('adaptive-status',result)
    return result


def learn_after_watering(plant, zone, at):
    plan = plant.get('adaptivePlan')
    if plant.get('carePlanMode')!='Intelligente' or not plan or plan.get('revisionSource') in ['AI','Modifica manuale']: return
    summary = learning(plant,plan.get('verdantWateringDays') or plan['wateringDays'],zone)
    plan['careLearning'] = summary
    if summary:
        summary['updatedAt'] = iso(at)
        plan.update(wateringDays=summary['learnedIntervalDays'],revisionSource='Apprendimento dalle cure',revisedAt=summary['updatedAt'])
        plant['wateringInterval'] = summary['learnedIntervalDays']
