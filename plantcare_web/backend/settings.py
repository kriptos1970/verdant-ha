import json
import os
from pathlib import Path
from zoneinfo import ZoneInfo
from . import __version__

class Settings:
    def __init__(self):
        path=Path(os.getenv('PLANTCARE_OPTIONS','/data/options.json'))
        self.options=json.loads(path.read_text()) if path.exists() else {}
        self.directory=os.getenv('PLANTCARE_DATA','.data')
        self.photo_directory=os.getenv('PLANTCARE_PHOTOS') or self.options.get('photo_directory') or str(Path(self.directory)/'photos')
        self.ingress=os.getenv('PLANTCARE_INGRESS','0')=='1'
        self.zone=self.options.get('timezone','Europe/Rome')
        ZoneInfo(self.zone)
        self.token=os.getenv('SUPERVISOR_TOKEN','')
        self.ha_url=os.getenv('PLANTCARE_HA_URL','http://supervisor/core/api')

    def public(self):
        provider=self.options.get('ai_provider','none')
        return {'version':__version__,'timezone':self.zone,'ingress':self.ingress,'aiProvider':provider,'aiModel':self.options.get('ai_model') or ('gemini-3.5-flash-lite' if provider=='gemini' else 'gpt-5-nano' if provider=='openai' else ''),'aiConfigured':bool(self.options.get('gemini_api_key' if provider=='gemini' else 'openai_api_key')) if provider!='none' else False,'autoApplyAI':self.options.get('auto_apply_ai',False),'aiUpdateTime':self.options.get('ai_update_time','03:00'),'sensorsConfigured':bool(self.token),'exposedEntities':self.options.get('exposed_entities',[]),'photoDirectory':self.photo_directory,'measurementRetentionDays':self.options.get('measurement_retention_days',365),'services':{**{k:bool(self.options.get(k+'_api_key')) for k in ['plantnet','perenual']},'openplantbook':bool(self.options.get('openplantbook_client_id') and self.options.get('openplantbook_secret'))}}
