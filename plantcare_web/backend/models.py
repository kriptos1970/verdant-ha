from typing import Any, Literal
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from .domain import KINDS, EXTRA_KINDS, iso, now, parse
from .care_kinds import canonical_event, canonical_kind, canonical_health

class Plant(BaseModel):
    model_config = ConfigDict(extra='allow')
    id: str = Field(default_factory=lambda:str(uuid4()).upper())
    name: str = Field(min_length=1, max_length=200)
    species: str = Field(default='', max_length=300)
    family: str | None = Field(default=None,max_length=300)
    room: str = Field(default='Casa', min_length=1, max_length=200)
    category: Literal['Tropicale','Succulenta','Aromatica','Fiorita','Altro'] = 'Tropicale'
    light: Literal['Luce bassa','Luce indiretta','Luce intensa','Sole diretto'] = 'Luce indiretta'
    wateringInterval: int = Field(default=7, ge=1, le=120)
    fertilizingInterval: int | None = Field(default=None, ge=1, le=365)
    rotationInterval: int | None = Field(default=None, ge=1, le=3650)
    repottingInterval: int | None = Field(default=None, ge=1, le=3650)
    pruningInterval: int | None = Field(default=None, ge=1, le=3650)
    inspectionInterval: int | None = Field(default=None, ge=1, le=3650)
    progressInterval: int | None = Field(default=None, ge=1, le=3650)
    acquiredOn: str = Field(default_factory=lambda:iso(now()))
    lastWatered: str = Field(default_factory=lambda:iso(now()))
    notes: str = Field(default='', max_length=20000)
    symbol: str = 'leaf.fill'
    history: list[dict[str, Any]] = Field(default_factory=list)
    carePlanMode: Literal['Manuale','Intelligente','AI'] | None = 'Manuale'

    @field_validator('name','room')
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError('Campo obbligatorio')
        return value.strip()

    @field_validator('acquiredOn','lastWatered')
    @classmethod
    def date(cls,value):
        return iso(parse(value))

    @field_validator('history')
    @classmethod
    def history_valid(cls, value):
        seen=set()
        result=[]
        for event in value:
            event=canonical_event(event)
            UUID(event['id'])
            if event['id'] in seen:
                raise ValueError('Evento duplicato')
            seen.add(event['id'])
            if event.get('kind') not in set(KINDS) | EXTRA_KINDS:
                raise ValueError('Tipo di cura sconosciuto')
            if event.get('status') not in (None,'completed','postponed'):
                raise ValueError('Stato cura non valido')
            for key in ['date','deletedAt','postponedUntil']:
                if event.get(key):
                    parse(event[key])
            result.append(event)
        return result

class Product(BaseModel):
    model_config = ConfigDict(extra='allow')
    id: str = Field(default_factory=lambda:str(uuid4()).upper())
    name: str = Field(min_length=1,max_length=200)
    brand: str = Field(default='',max_length=200)
    form: Literal['Liquido','Granulare','Bastoncini','Polvere','Organico','Altro'] = 'Liquido'
    category: Literal['Fertilizzante','Radicante','Antiparassitario','Fungicida','Biostimolante','Ammendante','Altro trattamento'] | None = 'Fertilizzante'
    dosage: str = Field(default='',max_length=2000)
    applicationMethod: str = Field(default='',max_length=2000)
    suitableFor: str = Field(default='',max_length=2000)
    applicationFrequency: str = Field(default='',max_length=200)
    notes: str = Field(default='',max_length=20000)
    applicationIntervalDays: int | None = Field(default=None,ge=1,le=365)

class EventRequest(BaseModel):
    id: str = Field(default_factory=lambda:str(uuid4()).upper())
    kind: str
    date: str = Field(default_factory=lambda:iso(now()))
    status: Literal['completed','postponed'] = 'completed'
    postponedUntil: str | None = None
    note: str = Field(default='',max_length=20000)
    photoPaths: list[str] = Field(default_factory=list,max_length=50)
    includingFertilizing: bool = False
    treatmentPlanID: str | None = None
    productID: str | None = None
    expectedApplicationNumber: int | None = Field(default=None,ge=1,le=100)
    scheduledDueDate: str | None = None
    health: str | None = None
    @field_validator('id')
    @classmethod
    def identifier(cls,value):
        UUID(value)
        return value
    @field_validator('kind')
    @classmethod
    def kind_valid(cls,value):
        return canonical_kind(value)
    @field_validator('health')
    @classmethod
    def health_valid(cls,value):
        return canonical_health(value) if value else None
    @field_validator('date','postponedUntil','scheduledDueDate')
    @classmethod
    def date_valid(cls,value):
        return iso(parse(value)) if value else None

class Question(BaseModel):
    question: str = Field(min_length=1,max_length=4000)
    @field_validator('question')
    @classmethod
    def not_blank(cls,value):
        if not value.strip():raise ValueError('Scrivi una domanda.')
        return value.strip()

class LanguagePreference(BaseModel):
    language: Literal['auto','it','en'] | None = None
    experience: Literal['principiante','intermedio','esperto','professionista'] | None = None

class Mapping(BaseModel):
    entityID: str = Field(min_length=1,max_length=200)
    plantID: str | None = None
    room: str | None = None

class Measurement(BaseModel):
    kind: Literal['illuminance','moisture','temperature','humidity','conductivity']
    value: float = Field(allow_inf_nan=False)
    unit: str = Field(max_length=30)
    date: str = Field(default_factory=lambda:iso(now()))
    @field_validator('date')
    @classmethod
    def date_valid(cls,value):
        return iso(parse(value))
    @model_validator(mode='after')
    def physical_measurement(self):
        expected={'illuminance':{'lx','lux'},'moisture':{'%'},'humidity':{'%'},'temperature':{'°C'},'conductivity':{'µS/cm','μS/cm','uS/cm'}}
        if self.unit not in expected[self.kind]: raise ValueError('Unità non valida per questa misura.')
        if self.kind in {'moisture','humidity'} and not 0<=self.value<=100: raise ValueError('La percentuale deve essere tra 0 e 100.')
        if self.kind in {'illuminance','conductivity'} and self.value<0: raise ValueError('La misura non può essere negativa.')
        if self.kind=='temperature' and not -90<=self.value<=65: raise ValueError('Temperatura fuori intervallo.')
        return self


class TreatmentInput(BaseModel):
    id: str = Field(default_factory=lambda:str(uuid4()).upper())
    productID: str
    startDate: str
    intervalDays: int = Field(ge=1,le=365)
    totalApplications: int = Field(ge=1,le=100)
    endDate: str | None = None
    dose: str = Field(default='',max_length=2000)
    notes: str = Field(default='',max_length=20000)

    @field_validator('id','productID')
    @classmethod
    def identifier(cls,value):
        UUID(value)
        return value

    @field_validator('startDate','endDate')
    @classmethod
    def date_valid(cls,value):
        return iso(parse(value)) if value else None

    @model_validator(mode='after')
    def dates_valid(self):
        if self.endDate and parse(self.endDate)<parse(self.startDate):
            raise ValueError('La data finale deve essere uguale o successiva al primo intervento.')
        return self


class RoundCommand(BaseModel):
    plantID: str
    eventID: str
    expectedActionID: str = Field(min_length=1,max_length=500)
    operation: Literal['complete','postpone']
    includingFertilizing: bool = False
    note: str = Field(default='',max_length=20000)

    @field_validator('plantID','eventID')
    @classmethod
    def identifier(cls,value):
        UUID(value)
        return value

class CareLocation(BaseModel):
    name: str = Field(min_length=1,max_length=200)
    detail: str = Field(default='',max_length=300)
    latitude: float = Field(ge=-90,le=90,allow_inf_nan=False)
    longitude: float = Field(ge=-180,le=180,allow_inf_nan=False)

class ClimateInput(BaseModel):
    averageTemperature: float = Field(ge=-90,le=65,allow_inf_nan=False)
    relativeHumidity: int = Field(ge=0,le=100)
    precipitationNextWeek: float = Field(ge=0,le=5000,allow_inf_nan=False)

class PhotoCleanupRequest(BaseModel):
    names: list[str] = Field(default_factory=list, max_length=10000)

class MoveRequest(BaseModel):
    room: str = Field(min_length=1, max_length=200)
    placement: Literal['Balcone riparato','Pieno sole','Ombra','Mezza ombra · balcone','Patio','Pianerottolo','Interno luminoso','Interno poco luminoso']
    date: str = Field(default_factory=lambda:iso(now()))
    note: str = Field(default='',max_length=2000)
    version: int = Field(ge=1)
    @field_validator('room')
    @classmethod
    def room_not_blank(cls,value):
        if not value.strip():raise ValueError('Campo obbligatorio')
        return value.strip()
    @field_validator('date')
    @classmethod
    def date_valid(cls,value):
        return iso(parse(value))

class AdaptiveRequest(BaseModel):
    botanicalPreviewID: str | None = Field(default=None,max_length=100)
    confirmBotanicalMatch: bool = False
    location: CareLocation
    placement: Literal['Balcone riparato','Pieno sole','Ombra','Mezza ombra · balcone','Patio','Pianerottolo','Interno luminoso','Interno poco luminoso']
    weatherEnabled: bool = False
    climate: ClimateInput | None = None
    @model_validator(mode='after')
    def climate_required(self):
        if not self.weatherEnabled and self.climate is None:
            raise ValueError('Indica il clima oppure abilita il meteo Open-Meteo.')
        return self

class AIModelSelection(BaseModel):
    model: str = Field(min_length=1,max_length=200,pattern=r'^[A-Za-z0-9_.:-]+$')

class AdviceSelection(BaseModel):
    adviceID: str = Field(min_length=1,max_length=100)
    watering: bool = False
    fertilizing: bool = False
    inspection: bool = False
    pruning: bool = False
    repotting: bool = False

class PhotoAnnotation(BaseModel):
    model_config=ConfigDict(extra='forbid')
    id: str = Field(default_factory=lambda:str(uuid4()).upper())
    x: float = Field(ge=0,le=1,allow_inf_nan=False)
    y: float = Field(ge=0,le=1,allow_inf_nan=False)
    note: str = Field(default='Zona da controllare',max_length=2000)

class HealthPhoto(BaseModel):
    model_config=ConfigDict(extra='forbid')
    id: str = Field(default_factory=lambda:str(uuid4()).upper())
    angle: Literal['Foglia · sopra','Foglia · sotto','Fusto','Terreno']
    path: str = Field(pattern=r'^[a-f0-9]{64}\.jpg$')
    annotations: list[PhotoAnnotation] = Field(default_factory=list,max_length=50)

class HealthPhotoSession(BaseModel):
    model_config=ConfigDict(extra='forbid')
    id: str = Field(default_factory=lambda:str(uuid4()).upper())
    date: str = Field(default_factory=lambda:iso(now()))
    health: str = 'good'
    note: str = Field(default='',max_length=20000)
    photos: list[HealthPhoto] = Field(min_length=4,max_length=4)

    @field_validator('id')
    @classmethod
    def session_id(cls,value): return str(UUID(value)).upper()

    @field_validator('health')
    @classmethod
    def session_health(cls,value): return canonical_health(value)

    @field_validator('date')
    @classmethod
    def session_date(cls,value): return iso(parse(value))

    @model_validator(mode='after')
    def complete_angles(self):
        if {p.angle for p in self.photos}!={'Foglia · sopra','Foglia · sotto','Fusto','Terreno'}:
            raise ValueError('Completa le quattro inquadrature, senza duplicati.')
        if len({p.id for p in self.photos})!=4:raise ValueError('Identificativo fotografia duplicato.')
        for photo in self.photos:
            if len({a.id for a in photo.annotations})!=len(photo.annotations):raise ValueError('Annotazione duplicata.')
        return self
