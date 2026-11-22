"""Run the web UI with isolated native-style demo data; no operational archive."""
import argparse
from datetime import timedelta
import os
from pathlib import Path
import sys
import tempfile
from uuid import uuid4


def run():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=8770)
    parser.add_argument('--plant-photo',type=Path)
    parser.add_argument('--paired-care',action='store_true',help='Include grouped water/feed and optional summary rows in isolated demo')
    parser.add_argument('--product-photo',type=Path)
    args=parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='plantcare-ios-preview-') as directory:
        os.environ.update(PLANTCARE_DATA=directory,PLANTCARE_PHOTOS=directory+'/photos',PLANTCARE_OPTIONS=directory+'/options.json',PLANTCARE_MIGRATE_DIR=directory+'/migration',PLANTCARE_INGRESS='0',SUPERVISOR_TOKEN='')
        sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
        from plantcare_web.backend import main
        from plantcare_web.backend.domain import now,iso
        from plantcare_web.backend.models import Plant,Product
        import uvicorn
        main.settings.options={};main.settings.token=''
        for name,species,room,category,light,interval,elapsed,note in [
            ('Olivia','Monstera deliciosa','Soggiorno','Tropicale','Luce indiretta',7,6,'Ama l’umidità. Pulisci le foglie una volta al mese.'),
            ('Pico','Pilea peperomioides','Studio','Tropicale','Luce intensa',6,7,'Ruotare di un quarto di giro ogni settimana.'),
            ('Nora','Sansevieria trifasciata','Camera','Succulenta','Luce bassa',18,10,'Lasciare asciugare completamente il terriccio.'),
            ('Basil','Ocimum basilicum','Cucina','Aromatica','Sole diretto',3,1,'Raccogliere le foglie dall’alto per favorire la crescita.')]:
            plant=Plant(name=name,species=species,room=room,category=category,light=light,wateringInterval=interval,lastWatered=iso(now()-timedelta(days=elapsed)),acquiredOn=iso(now()-timedelta(days=270)),notes=note).model_dump()
            if name=='Olivia':
                if args.paired_care:
                    plant.update(fertilizingInterval=7,lastFertilized=plant['lastWatered'],inspectionInterval=14,progressInterval=30,heightCM=58,potMaterial='Terracotta',potDiameterCM=20)
                plant['history']=[dict(id=str(uuid4()).upper(),kind='Annaffia',date=iso(now()-timedelta(days=6)),status='completed')]
                if args.paired_care:
                    completed=iso(now()-timedelta(days=5))
                    plant['lastWatered']=completed;plant['lastFertilized']=completed;plant['history'][0]['date']=completed
                    plant['history'].extend([dict(id=str(uuid4()).upper(),kind=kind,date=iso(now()-timedelta(days=days)),status='completed') for kind,days in [('Controlla salute',7),('Aggiorna progressi',16)]])
                if args.plant_photo:plant['photoPath']=main.store.write_photo(args.plant_photo)
            main.store.put('plants',plant)
        product=Product(name='Prodotto dimostrativo',brand='Anteprima locale',dosage='Da etichetta',notes='Dati di collaudo: non applicare alle piante reali.').model_dump()
        if args.product_photo:product['photoPath']=main.store.write_photo(args.product_photo)
        if args.paired_care:product['dosage']='10–20 ml per 1 litro'
        main.store.put('fertilizers',product)
        if args.paired_care:
            for plant,version in main.store.list('plants'):
                if plant['name']=='Olivia':
                    plant.update(fertilizerProductID=product['id'],fertilizerDose='½ dose',growthEntries=[dict(id=str(uuid4()).upper(),date=iso(now()-timedelta(days=2)),health='Buona',note='Aggiornamento dimostrativo separato dalla cronologia delle cure.',photoPaths=[],heightCM=58)])
                    main.store.put('plants',plant,version)
        uvicorn.run(main.app,host='127.0.0.1',port=args.port)

if __name__=='__main__':run()
