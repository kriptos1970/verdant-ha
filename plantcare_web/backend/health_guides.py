"""Read-only port of DiagnosisView and PlantKnowledgeGrid."""
from .adaptive import OUTDOOR
from .domain import swift_round

SYMPTOMS = ['Foglie gialle', 'Punte secche', 'Foglie cadenti', 'Macchie', 'Insetti', 'Crescita lenta']


def diagnosis(symptoms, language='it'):
    if not symptoms or any(s not in SYMPTOMS for s in symptoms):
        raise ValueError('Choose at least one available symptom.' if language=='en' else 'Scegli almeno un sintomo tra quelli disponibili.')
    if language=='en':
        if 'Foglie gialle' in symptoms:
            return 'Yellow leaves are often linked to overwatering. Let the substrate dry and check that the pot drains well.'
        if 'Punte secche' in symptoms or 'Foglie cadenti' in symptoms:
            return 'Check moisture a few centimetres deep. If the substrate is dry, water slowly and let it drain.'
        if 'Macchie' in symptoms or 'Insetti' in symptoms:
            return 'Temporarily isolate the plant, remove badly affected parts and inspect leaves and stem closely.'
        return 'Observe light, humidity and recent changes. Avoid drastic action until you have identified a likely cause.'
    if 'Foglie gialle' in symptoms:
        return 'Le foglie gialle sono spesso legate a troppa acqua. Lascia asciugare il terreno e verifica che il vaso dreni bene.'
    if 'Punte secche' in symptoms or 'Foglie cadenti' in symptoms:
        return 'Controlla l’umidità a qualche centimetro di profondità. Se il terreno è asciutto, annaffia lentamente e lascia scolare.'
    if 'Macchie' in symptoms or 'Insetti' in symptoms:
        return 'Isola temporaneamente la pianta, rimuovi le parti molto colpite e osserva da vicino foglie e fusto.'
    return 'Osserva luce, umidità e cambiamenti recenti. Evita interventi drastici finché non hai identificato una causa probabile.'


def practical_guide(plant, language='it'):
    category=plant['category'];tropical=category=='Tropicale';succulent=category=='Succulenta';aromatic=category=='Aromatica'
    en=language=='en'
    temperatures={'Tropicale':('18–30 °C','12–34 °C'),'Succulenta':('10–32 °C','5–38 °C'),'Aromatica':('12–28 °C','6–34 °C'),'Fiorita':('16–26 °C','10–32 °C'),'Altro':('15–28 °C','8–34 °C')}
    temperature,tolerable=temperatures[category]
    humidity='Media–alta · 55–75%' if tropical else 'Bassa · 30–50%' if succulent else 'Media · 40–60%'
    humidity_tolerable='40–85%' if tropical else '20–60%' if succulent else '30–70%'
    if en:
        humidity='Medium–high · 55–75%' if tropical else 'Low · 30–50%' if succulent else 'Medium · 40–60%'
    light=plant['light']
    light_names={'Luce bassa':'Low light','Luce indiretta':'Indirect light','Luce intensa':'Bright light','Sole diretto':'Direct sun'} if en else {'Luce bassa':'Luce bassa','Luce indiretta':'Luce indiretta','Luce intensa':'Luce intensa','Sole diretto':'Sole diretto'}
    light_tolerable={'Luce bassa':'Luce indiretta','Luce indiretta':'Luce bassa o intensa','Luce intensa':'Luce indiretta','Sole diretto':'Luce intensa'}[light]
    if en:
        light_tolerable={'Luce bassa':'Indirect light','Luce indiretta':'Low or bright light','Luce intensa':'Indirect light','Sole diretto':'Bright light'}[light]
        light_tip='Acclimatise gradually to strong sun.' if light=='Sole diretto' else 'Rotate the pot every week for even growth.'
        humidity_tip='Group plants together; do not leave water on the leaves.' if tropical else 'Ensure good ventilation.'
        tiles=[
            ('Substrate','Cactus substrate' if succulent else 'Airy aroid mix' if plant.get('family')=='Araceae' else 'Draining potting mix','Warning: the pot has no drainage.' if plant.get('potHasDrainage') is False else 'Let the water drain completely.'),
            ('Fertilizing',plant.get('fertilizerType') if plant.get('fertilizerType') is not None else 'Succulent fertilizer' if succulent else 'Balanced liquid','Apply only to already moist substrate.'),
            ('Pruning','Regular pinching' if aromatic else 'Dry or damaged leaves','Use clean scissors and remove damaged parts.'),
            ('Repotting','Every 2–3 years' if succulent else 'Every 1–2 years','Prefer early spring and a slightly larger pot.'),
            ('Propagation','Leaf cutting or offset' if succulent else 'Apical cutting' if aromatic else 'Cutting or division','The best time is when growth resumes.'),
            ('Difficulty','Medium' if tropical or category=='Fiorita' else 'Easy',humidity_tip if tropical else light_tip),
        ]
    else:
        light_tip='Acclimata gradualmente al sole forte.' if light=='Sole diretto' else 'Ruota il vaso ogni settimana per una crescita uniforme.'
        humidity_tip='Raggruppa le piante; non lasciare acqua sulle foglie.' if tropical else 'Garantisci una buona ventilazione.'
        tiles=[
            ('Terreno','Substrato per cactus' if succulent else 'Mix arioso per aroidi' if plant.get('family')=='Araceae' else 'Terriccio drenante','Attenzione: il vaso non ha drenaggio.' if plant.get('potHasDrainage') is False else 'Lascia defluire completamente l’acqua.'),
            ('Concimazione',plant.get('fertilizerType') if plant.get('fertilizerType') is not None else 'Concime per succulente' if succulent else 'Liquido bilanciato','Somministra solo su terreno già umido.'),
            ('Potatura','Cimatura regolare' if aromatic else 'Foglie secche o danneggiate','Usa forbici pulite e rimuovi parti danneggiate.'),
            ('Rinvaso','Ogni 2–3 anni' if succulent else 'Ogni 1–2 anni','Preferisci l’inizio della primavera e un vaso poco più grande.'),
            ('Propagazione','Talea di foglia o pollone' if succulent else 'Talea apicale' if aromatic else 'Talea o divisione','Il periodo migliore è la ripresa vegetativa.'),
            ('Difficoltà','Media' if tropical or category=='Fiorita' else 'Facile',humidity_tip if tropical else light_tip),
        ]
    outdoor=(plant.get('adaptivePlan') or {}).get('placement') in OUTDOOR
    seasonal=[]
    for month in range(1,13):
        multiplier=(2.4 if succulent else 1.8) if month in (12,1,2) else 1.3 if month in (3,4,10,11) else (.65 if outdoor else .82) if month in (6,7,8) else 1
        seasonal.append({'month':month,'days':max(1,swift_round(plant['wateringInterval']*multiplier))})
    return {'ranges':[{'title':'Light' if en else 'Luce','ideal':light_names[light],'tolerable':light_tolerable},{'title':'Temperature' if en else 'Temperatura','ideal':temperature,'tolerable':tolerable},{'title':'Humidity' if en else 'Umidità','ideal':humidity,'tolerable':humidity_tolerable}], 'tiles':[dict(title=t,value=v,tip=tip) for t,v,tip in tiles], 'seasonal':seasonal}
