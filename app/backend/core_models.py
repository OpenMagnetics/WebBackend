from pydantic import BaseModel
from typing import Optional, Dict, Union, List
from enum import Enum


class Utils(BaseModel):
    class Config:  
        use_enum_values = True
    """A dimension of the wire, in m"""
    """The maximum value of the dimension, in m"""
    maximum: Optional[float] = None
    """The minimum value of the dimension, in m"""
    minimum: Optional[float] = None
    """The nominal value of the dimension, in m"""
    nominal: Optional[float] = None


class CoreBobbinFamily(str, Enum):
    """The family of a magnetic shape"""
    e = "e"
    ec = "ec"
    eer = "eer"
    efd = "efd"
    el = "el"
    ep = "ep"
    er = "er"
    etd = "etd"
    p = "p"
    pm = "pm"
    pq = "pq"
    rm = "rm"
    u = "u"
    ut = "ut"


class Status(str, Enum):
    """The production status of a part according to its manufacturer"""
    obsolete = "obsolete"
    production = "production"
    prototype = "prototype"


class ManufacturerInfo(BaseModel):
    class Config:  
        use_enum_values = True
    """Data from the manufacturer for a given part"""
    """The name of the manufacturer of the part"""
    name: str
    """The manufacturer's price for this part"""
    cost: Optional[str] = None
    """The manufacturer's reference of this part"""
    reference: Optional[str] = None
    """The production status of a part according to its manufacturer"""
    status: Optional[Status] = None


class ProcessedData(BaseModel):
    class Config:  
        use_enum_values = True
    """TBD, add separators"""
    """The thicknes of the central column wall, where the wire is wound"""
    columnThickness: Optional[float] = None
    """The thicknes of the walls that hold the wire on both sides of the column"""
    wallThickness: Optional[float] = None


class CoreBobbinType(str, Enum):
    """The type of a magnetic shape"""
    custom = "custom"
    standard = "standard"


class CoreBobbin(BaseModel):
    class Config:  
        use_enum_values = True
    """A shape for the magnetic cores"""
    """The family of a magnetic shape"""
    family: CoreBobbinFamily
    """The type of a magnetic shape"""
    type: CoreBobbinType
    """The dimensions of a magnetic shape, keys must be as defined in EN 62317"""
    dimensions: Optional[Dict[str, Union[Utils, float]]] = None
    """The subtype of the shape, in case there are more than one"""
    familySubtype: Optional[str] = None
    manufacturerInfo: Optional[ManufacturerInfo] = None
    """The name of a magnetic shape, according to EN 62317"""
    name: Optional[str] = None
    """TBD, add separators"""
    processedData: Optional[ProcessedData] = None
    """The name of a magnetic shape that this bobbin belongs to"""
    shape: Optional[str] = None


class ShapeEnum(str, Enum):
    """Shape of the column, also used for gaps"""
    irregular = "irregular"
    oblong = "oblong"
    rectangular = "rectangular"
    round = "round"


class GappingType(str, Enum):
    """The type of a gap"""
    additive = "additive"
    residual = "residual"
    subtractive = "subtractive"


class CoreGap(BaseModel):
    class Config:  
        use_enum_values = True
    """A gap for the magnetic cores"""
    """The length of the gap"""
    length: float
    """The type of a gap"""
    type: GappingType
    """Geometrical area of the gap"""
    area: Optional[float] = None
    """The coordinates of the center of the gap, referred to the center of thw main column"""
    coordinates: Optional[List[float]] = None
    """The distance where the closest perpendicular surface is. This usually is half the winding
    height
    """
    distanceClosestNormalSurface: Optional[float] = None
    """Dimension of the section normal to the magnetic flux"""
    sectionDimensions: Optional[List[float]] = None
    shape: Optional[ShapeEnum] = None


class BhCycleElement(BaseModel):
    class Config:  
        use_enum_values = True
    """data for describing one point of the BH cycle"""
    """magnetic field value, in A/m"""
    magneticField: float
    """magnetic flux density value, in T"""
    magneticFluxDensity: float
    """temperature for the field value, in Celsius"""
    temperature: float


class PurpleComposition(str, Enum):
    """The composition of a magnetic material"""
    amorphous = "amorphous"
    electricalSteel = "electricalSteel"
    ferrite = "ferrite"
    nanocrystaline = "nanocrystaline"
    powder = "powder"


class InitialElement(BaseModel):
    class Config:  
        use_enum_values = True
    """data for describing one point of permebility"""
    """Permeability value"""
    value: float
    """magnetic flux density peak for the field value, in T"""
    magneticFluxDensityPeak: Optional[float] = None
    """temperature for the field value, in Celsius"""
    temperature: Optional[float] = None
    """tolerance for the field value"""
    tolerance: Optional[float] = None


class Permeability(BaseModel):
    class Config:  
        use_enum_values = True
    """The data regarding the permeability of a magnetic material"""
    """The initial permeability of a magnetic material according to its manufacturer"""
    initial: List[InitialElement]
    """The amplitude permeability of a magnetic material according to its manufacturer"""
    amplitude: Optional[List[InitialElement]] = None


class CoreMaterialType(str, Enum):
    """The type of a magnetic material"""
    commercial = "commercial"
    custom = "custom"


class VolumetricLossElement(BaseModel):
    class Config:  
        use_enum_values = True
    """data for describing the volumetric losses at a given point of magnetic flux density,
    frequency and temperature
    
    List of volumetric losses points
    """
    """frequency value, in Hz"""
    frequency: float
    """magnetic flux density value, in T"""
    magneticFluxDensity: float
    """temperature value, in Celsius"""
    temperature: float
    """voluemtric losses value, in W/m3"""
    volumetricLosses: float


class Resistivity(BaseModel):
    class Config:  
        use_enum_values = True
    """Resistivity value according to manufacturer
    
    data for describing one point of resistivity
    """
    """Resistivity value, in Ohm * m"""
    value: float
    """temperature for the field value, in Celsius"""
    temperature: Optional[float] = None


class VolumetricLossesClass(BaseModel):
    class Config:  
        use_enum_values = True
    """Steinmetz coefficients for estimating volumetric losses in a given frequency range
    
    Roshen coefficients for estimating volumetric losses
    """
    """Name of this method"""
    method: str
    """frequency power coefficient alpha"""
    alpha: Optional[float] = None
    """magnetic flux density power coefficient beta"""
    beta: Optional[float] = None
    """Constant temperature coefficient ct0"""
    ct0: Optional[float] = None
    """Proportional negative temperature coefficient ct1"""
    ct1: Optional[float] = None
    """Square temperature coefficient ct2"""
    ct2: Optional[float] = None
    """Proportional coefficient k"""
    k: Optional[float] = None
    """maximum frequency for which the coefficients are valid, in Hz"""
    maximumFrequency: Optional[float] = None
    """minimum frequency for which the coefficients are valid, in Hz"""
    minimumFrequency: Optional[float] = None
    """BH Cycle points where the magnetic flux density is 0"""
    coerciveforce: Optional[List[BhCycleElement]] = None
    """List of reference volumetric losses used to estimate excess eddy current losses"""
    referenceVolumetricLosses: Optional[List[VolumetricLossElement]] = None
    """BH Cycle points where the magnetic field is 0"""
    remanence: Optional[List[BhCycleElement]] = None
    """Resistivity value according to manufacturer"""
    resistivity: Optional[Resistivity] = None
    """BH Cycle points where a non-negligible increase in magnetic field produces a negligible
    increase of magnetic flux density
    """
    saturation: Optional[List[BhCycleElement]] = None


class CoreMaterial(BaseModel):
    class Config:  
        use_enum_values = True
    """A material for the magnetic cores"""
    """The composition of a magnetic material"""
    composition: PurpleComposition
    manufacturerInfo: ManufacturerInfo
    """The name of a magnetic material"""
    name: str
    """The type of a magnetic material"""
    type: CoreMaterialType
    volumetricLosses: Union[List[VolumetricLossElement], VolumetricLossesClass]
    bhCycle: Optional[List[BhCycleElement]] = None
    """The family of a magnetic material according to its manufacturer"""
    family: Optional[str] = None
    """The data regarding the permeability of a magnetic material"""
    permeability: Optional[Permeability] = None


class CoreShapeFamily(str, Enum):
    """The family of a magnetic shape"""
    e = "e"
    ec = "ec"
    efd = "efd"
    el = "el"
    ep = "ep"
    epx = "epx"
    eq = "eq"
    er = "er"
    etd = "etd"
    lp = "lp"
    p = "p"
    planare = "planar e"
    planarel = "planar el"
    planarer = "planar er"
    pm = "pm"
    pq = "pq"
    rm = "rm"
    u = "u"
    ui = "ui"
    ur = "ur"
    ut = "ut"


class CoreShape(BaseModel):
    class Config:  
        use_enum_values = True
    """A shape for the magnetic cores"""
    """The family of a magnetic shape"""
    family: CoreShapeFamily
    """The type of a magnetic shape"""
    type: CoreBobbinType
    """Alternative names of a magnetic shape"""
    aliases: Optional[List[str]] = None
    """The dimensions of a magnetic shape, keys must be as defined in EN 62317"""
    dimensions: Optional[Dict[str, Union[Utils, float]]] = None
    """The subtype of the shape, in case there are more than one"""
    familySubtype: Optional[str] = None
    """The name of a magnetic shape"""
    name: Optional[str] = None


class FunctionalDescriptionType(str, Enum):
    """The type of core"""
    pieceandplate = "piece and plate"
    toroidal = "toroidal"
    twopieceset = "two-piece set"
    closedshape = "closed shape"


class FunctionalDescription(BaseModel):
    class Config:  
        use_enum_values = True
    """The data from the core based on its function, in a way that can be used by analytical
    models.
    """
    bobbin: Union[CoreBobbin, None, str]
    """The lists of gaps in the magnetic core"""
    gapping: List[CoreGap]
    material: Union[CoreMaterial, str]
    shape: Union[CoreShape, str]
    """The type of core"""
    type: FunctionalDescriptionType
    """The name of core"""
    name: Optional[str] = None
    """The number of stacked cores"""
    numberStacks: Optional[int] = None


class MachiningElement(BaseModel):
    class Config:  
        use_enum_values = True
    """Data describing the machining applied to a piece"""
    """The coordinates of the start of the machining, referred to the top of the main column of
    the piece
    """
    coordinates: List[float]
    """Length of the machining"""
    length: float


class InsulationMaterialComposition(str, Enum):
    """The composition of a magnetic material
    
    The composition of a insulation material
    """
    air = "air"
    amorphous = "amorphous"
    bakelite = "bakelite"
    electricalSteel = "electricalSteel"
    ferrite = "ferrite"
    nanocrystaline = "nanocrystaline"
    nylon = "nylon"
    paper = "paper"
    polyimide = "polyimide"
    polystyrene = "polystyrene"
    powder = "powder"
    teflon = "teflon"


class DielectricStrengthElement(BaseModel):
    class Config:  
        use_enum_values = True
    """data for describing one point of dieletric strength"""
    """Dieletric strength value, in V / m"""
    value: float
    """Humidity for the field value, in proportion over 1"""
    humidity: Optional[float] = None
    """Thickness of the material"""
    thickness: Optional[float] = None


class Rating(BaseModel):
    class Config:  
        use_enum_values = True
    """The rating of the material"""
    """The temperature rating of the material"""
    temperature: Optional[float] = None
    """The voltage rating of the material"""
    voltage: Optional[float] = None


class Material(BaseModel):
    class Config:  
        use_enum_values = True
    """A material for the magnetic cores
    
    A material for insulation
    """
    """The name of a magnetic material
    
    The name of a insulation material
    """
    name: str
    volumetricLosses: Union[List[VolumetricLossElement], VolumetricLossesClass, None]
    bhCycle: Optional[List[BhCycleElement]] = None
    """The composition of a magnetic material
    
    The composition of a insulation material
    """
    composition: Optional[InsulationMaterialComposition] = None
    """The family of a magnetic material according to its manufacturer"""
    family: Optional[str] = None
    manufacturerInfo: Optional[ManufacturerInfo] = None
    """The data regarding the permeability of a magnetic material"""
    permeability: Optional[Permeability] = None
    """The type of a magnetic material"""
    type: Optional[CoreMaterialType] = None
    dielectricStrength: Optional[List[DielectricStrengthElement]] = None
    """The manufacturer of the insulation material"""
    manufacturer: Optional[str] = None
    """The rating of the material"""
    rating: Optional[Rating] = None
    """The thermal conductivity of the insulation material, in W / m * K"""
    thermalConductivity: Optional[float] = None


class GeometricalDescriptionType(str, Enum):
    """The type of piece
    
    The type of spacer
    """
    halfset = "half set"
    plate = "plate"
    sheet = "sheet"
    spacer = "spacer"
    toroidal = "toroidal"
    closed = "closed"


class GeometricalDescription(BaseModel):
    class Config:  
        use_enum_values = True
    """Data describing the a piece of a core
    
    Data describing the spacer used to separate cores in additive gaps
    """
    """The coordinates of the top of the piece, referred to the center of the main column
    
    The coordinates of the center of the gap, referred to the center of the main column
    """
    coordinates: List[float]
    material: Union[Material, str]
    shape: Union[CoreShape, None, str]
    """The type of piece
    
    The type of spacer
    """
    type: GeometricalDescriptionType
    machining: Optional[List[MachiningElement]] = None
    """Dimensions of the cube defining the spacer"""
    dimensions: Optional[List[float]] = None


class ColumnType(str, Enum):
    """Name of the column"""
    central = "central"
    lateral = "lateral"


class ColumnElement(BaseModel):
    class Config:  
        use_enum_values = True
    """Data describing a column of the core"""
    """Area of the section column, normal to the magnetic flux direction"""
    area: float
    """The coordinates of the center of the column, referred to the center of the main column.
    In the case of half-sets, the center will be in the top point, where it would join
    another half-set
    """
    coordinates: List[float]
    """Depth of the column"""
    depth: float
    """Height of the column"""
    height: float
    shape: ShapeEnum
    """Name of the column"""
    type: ColumnType
    """Width of the column"""
    width: float


class EffectiveParameters(BaseModel):
    class Config:  
        use_enum_values = True
    """Effective data of the magnetic core"""
    """This is the equivalent section the that magnetic flux traverses, because the shape of the
    core is not uniform and its section changes along the path
    """
    effectiveArea: float
    """This is the equivalent length that the magnetic flux travels through the core."""
    effectiveLength: float
    """This is the product of the effective length by the effective area, and represents the
    equivalent volume that is magnetized by the field
    """
    effectiveVolume: float
    """This is the minimum area seen by the magnetic flux along its path"""
    minimumArea: float


class WindingWindowElement(BaseModel):
    class Config:  
        use_enum_values = True
    """List of rectangular winding windows
    
    It is the area between the winding column and the closest lateral column, and it
    represents the area where all the wires of the magnetic will have to fit, and
    equivalently, where all the current must circulate once, in the case of inductors, or
    twice, in the case of transformers
    
    List of radial winding windows
    
    It is the area between the delimited between a height from the surface of the toroidal
    core at a given angle, and it represents the area where all the wires of the magnetic
    will have to fit, and equivalently, where all the current must circulate once, in the
    case of inductors, or twice, in the case of transformers
    """
    """Area of the winding window"""
    area: Optional[float] = None
    """The coordinates of the center of the winding window, referred to the center of the main
    column. In the case of half-sets, the center will be in the top point, where it would
    join another half-set
    
    The coordinates of the point of the winding window where the middle height touches the
    main column, referred to the center of the main column. In the case of half-sets, the
    center will be in the top point, where it would join another half-set
    """
    coordinates: Optional[List[float]] = None
    """Vertical height of the winding window"""
    height: Optional[float] = None
    """Horizontal width of the winding window"""
    width: Optional[float] = None
    """Total angle of the window"""
    angle: Optional[float] = None
    """Radial height of the winding window"""
    radialHeight: Optional[float] = None


class ProcessedDescription(BaseModel):
    class Config:  
        use_enum_values = True
    """The data from the core after been processed, and ready to use by the analytical models"""
    """List of columns in the core"""
    columns: List[ColumnElement]
    """Total depth of the core"""
    depth: float
    effectiveParameters: EffectiveParameters
    """Total height of the core"""
    height: float
    """Total width of the core"""
    width: float
    """List of winding windows, all elements in the list must be of the same type"""
    windingWindows: List[WindingWindowElement]


class Core(BaseModel):
    class Config:  
        use_enum_values = True
    """The description of a magnetic core"""
    """The data from the core based on its function, in a way that can be used by analytical
    models.
    """
    functionalDescription: FunctionalDescription
    """The data from the core based on its geometrical description, in a way that can be used by
    CAD models.
    """
    geometricalDescription: Optional[List[GeometricalDescription]] = None
    """The data from the core after been processed, and ready to use by the analytical models"""
    processedDescription: Optional[ProcessedDescription] = None
