from pydantic import BaseModel
from typing import Optional, List, Dict, Union
from enum import Enum


class NumericRequirement(BaseModel):
    class Config:  
        use_enum_values = True
    """Required values for the altitude
    
    Required values for the magnetizing inductance
    
    Required values for the temperature that the magnetic can reach under operation
    
    Data describing a minimum, maximum or range requirement
    """
    """True is the maximum value must be excluded from the range"""
    excludeMaximum: Optional[bool] = None
    """True is the minimum value must be excluded from the range"""
    excludeMinimum: Optional[bool] = None
    """Maximum value of the requirement"""
    maximum: Optional[float] = None
    """Minimum value of the requirement"""
    minimum: Optional[float] = None
    """Nominal value of the requirement"""
    nominal: Optional[float] = None


class CTI(Enum):
    """Required CTI"""
    GroupI = "Group I"
    GroupII = "Group II"
    GroupIIIa = "Group IIIa"
    GroupIIIb = "Group IIIb"


class InsulationType(Enum):
    """Required type of insulation"""
    Basic = "Basic"
    Double = "Double"
    Functional = "Functional"
    Reinforced = "Reinforced"
    Supplementary = "Supplementary"


class OvervoltageCategory(Enum):
    """Required overvoltage category"""
    OVCI = "OVC-I"
    OVCII = "OVC-II"
    OVCIII = "OVC-III"
    OVCIV = "OVC-IV"


class PollutionDegree(Enum):
    """Required pollution for the magnetic to work under"""
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"



class DesignRequirements(BaseModel):
    class Config:  
        use_enum_values = True
    """Data describing the design requirements
    
    The list of requirement that must comply a given magnetic
    """
    """Required values for the magnetizing inductance"""
    magnetizingInductance: NumericRequirement
    """Required turns ratios between primary and the rest of windings"""
    turnsRatios: List[NumericRequirement]
    """Required values for the altitude"""
    altitude: Optional[NumericRequirement] = None
    """Required CTI"""
    cti: Optional[CTI] = None
    """Required type of insulation"""
    insulationType: Optional[InsulationType] = None
    """Required values for the leakage inductance"""
    leakageInductance: Optional[List[NumericRequirement]] = None
    """A label that identifies these Design Requirements"""
    name: Optional[str] = None
    """Required values for the temperature that the magnetic can reach under operation"""
    operationTemperature: Optional[NumericRequirement] = None
    """Required overvoltage category"""
    overvoltageCategory: Optional[OvervoltageCategory] = None
    """Required pollution for the magnetic to work under"""
    pollutionDegree: Optional[PollutionDegree] = None



class ForcedConvectionCooling(BaseModel):
    class Config:  
        use_enum_values = True
    """Relative Humidity of the ambient where the magnetic will operate
    
    Data describing a natural convection cooling
    
    Data describing a forced convection cooling
    """
    """Name of the fluid used"""
    fluid: Optional[str] = None
    """Temperature of the fluid. To be used only if different from ambient temperature"""
    temperature: Optional[float] = None
    velocity: Optional[List[float]] = None



class OperationConditions(BaseModel):
    class Config:  
        use_enum_values = True
    """The description of a magnetic operation conditions"""
    """Temperature of the ambient where the magnetic will operate"""
    ambientTemperature: float
    """Relative Humidity of the ambient where the magnetic will operate"""
    ambientRelativeHumidity: Optional[float] = None
    """Relative Humidity of the ambient where the magnetic will operate"""
    cooling: Optional[ForcedConvectionCooling] = None
    """A label that identifies this Operation Conditions"""
    name: Optional[str] = None



class Harmonics(BaseModel):
    class Config:  
        use_enum_values = True
    """Data containing the harmonics of the waveform, defined by a list of amplitudes and a list
    of frequencies
    """
    """List of amplitudes of the harmonics that compose the waveform"""
    amplitudes: List[float]
    """List of frequencies of the harmonics that compose the waveform"""
    frequencies: List[float]


class WaveformLabel(Enum):
    """Label of the waveform, if applicable. Used for common waveforms"""
    custom = "custom"
    flyback = "flyback"
    phaseshiftedfullbridge = "phase-shifted full bridge"
    sinusoidal = "sinusoidal"
    square = "square"
    squarewithdeadtime = "square with dead time"
    triangular = "triangular"



class Processed(BaseModel):
    class Config:  
        use_enum_values = True
    """Label of the waveform, if applicable. Used for common waveforms"""
    label: WaveformLabel
    """The offset value of the waveform, referred to 0"""
    offset: float
    """The effective frequency value of the AC component of the waveform, according to
    https://sci-hub.wf/https://ieeexplore.ieee.org/document/750181, Appendix C
    """
    acEffectiveFrequency: Optional[float] = None
    """The duty cycle of the waveform, if applicable"""
    dutyCycle: Optional[float] = None
    """The effective frequency value of the waveform, according to
    https://sci-hub.wf/https://ieeexplore.ieee.org/document/750181, Appendix C
    """
    effectiveFrequency: Optional[float] = None
    """The maximum positive value of the waveform"""
    peak: Optional[float] = None
    """The peak to peak value of the waveform"""
    peakToPeak: Optional[float] = None
    """The RMS value of the waveform"""
    rms: Optional[float] = None
    """The Total Harmonic Distortion of the waveform, according to
    https://en.wikipedia.org/wiki/Total_harmonic_distortion
    """
    thd: Optional[float] = None



class Waveform(BaseModel):
    class Config:  
        use_enum_values = True
    """Data containing the points that define an arbitrary waveform with equidistant points
    
    Data containing the points that define an arbitrary waveform with non-equidistant points
    paired with their time in the period
    """
    """List of values that compose the waveform, at equidistant times form each other"""
    data: List[float]
    """The number of periods covered by the data"""
    numberPeriods: Optional[int] = None
    ancillaryLabel: Optional[str] = None
    time: Optional[List[float]] = None



class ElectromagneticParameter(BaseModel):
    class Config:  
        use_enum_values = True
    """Structure definining one electromagnetic parameters: current, voltage, magnetic flux
    density
    """
    """Data containing the harmonics of the waveform, defined by a list of amplitudes and a list
    of frequencies
    """
    harmonics: Optional[Harmonics] = None
    processed: Optional[Processed] = None
    waveform: Optional[Waveform] = None



class OperationPointExcitation(BaseModel):
    class Config:  
        use_enum_values = True
    """Data describing the excitation of the winding
    
    The description of a magnetic operation point
    """
    """Frequency of the waveform, common for all electromagnetic parameters, in Hz"""
    frequency: float
    current: Optional[ElectromagneticParameter] = None
    magneticFieldStrength: Optional[ElectromagneticParameter] = None
    magneticFluxDensity: Optional[ElectromagneticParameter] = None
    magnetizingCurrent: Optional[ElectromagneticParameter] = None
    """A label that identifies this Operation Point"""
    name: Optional[str] = None
    voltage: Optional[ElectromagneticParameter] = None



class OperationPoint(BaseModel):
    class Config:  
        use_enum_values = True
    """Data describing one operation point, including the operation conditions and the
    excitations for all ports
    """
    conditions: OperationConditions
    excitationsPerWinding: List[OperationPointExcitation]
    """Name describing this operation point"""
    name: Optional[str] = None



class Inputs(BaseModel):
    class Config:  
        use_enum_values = True
    """The description of the inputs that can be used to design a Magnetic"""
    """Data describing the design requirements"""
    designRequirements: DesignRequirements
    """Data describing the operation points"""
    operationPoints: List[OperationPoint]


class ColumnShape(Enum):
    """Shape of the column, also used for gaps"""
    irregular = "irregular"
    oblong = "oblong"
    rectangular = "rectangular"
    round = "round"


class GapType(Enum):
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
    type: GapType
    """Geometrical area of the gap"""
    area: Optional[float] = None
    """The coordinates of the center of the gap, referred to the center of thw main column"""
    coordinates: Optional[List[float]] = None
    """The distance where the closest perpendicular surface is. This usually is half the winding
    height
    """
    distanceClosestNormalSurface: Optional[float] = None
    """The distance where the closest parallel surface is. This usually is the opposite side of
    the winnding window
    """
    distanceClosestParallelSurface: Optional[float] = None
    """Dimension of the section normal to the magnetic flux"""
    sectionDimensions: Optional[List[float]] = None
    shape: Optional[ColumnShape] = None



class SaturationElement(BaseModel):
    class Config:  
        use_enum_values = True
    """data for describing one point of the BH cycle"""
    """magnetic field value, in A/m"""
    magneticField: float
    """magnetic flux density value, in T"""
    magneticFluxDensity: float
    """temperature for the field value, in Celsius"""
    temperature: float


class Status(Enum):
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


class MaterialComposition(Enum):
    """The composition of a magnetic material"""
    amorphous = "amorphous"
    electricalSteel = "electricalSteel"
    ferrite = "ferrite"
    ironPowder = "ironPowder"
    nanocrystalline = "nanocrystalline"



class FrequencyFactor(BaseModel):
    class Config:  
        use_enum_values = True
    """Field with the coefficients used to calculate how much the permeability decreases with
    the frequency, as factor = a + b * f + c * pow(f, 2) + d * pow(f, 3) + e * pow(f, 4)
    """
    a: float
    b: float
    c: float
    d: float
    e: float



class MagneticFieldDcBiasFactor(BaseModel):
    class Config:  
        use_enum_values = True
    """Field with the coefficients used to calculate how much the permeability decreases with
    the H DC bias, as factor = a + b * pow(H, c)
    """
    a: float
    b: float
    c: float



class TemperatureFactor(BaseModel):
    class Config:  
        use_enum_values = True
    """Field with the coefficients used to calculate how much the permeability decreases with
    the temperature, as factor = a + b * T + c * pow(T, 2) + d * pow(T, 3) + e * pow(T, 4)
    """
    a: float
    b: float
    c: float
    d: float
    e: float



class MagneticsPermeabilityMethodData(BaseModel):
    class Config:  
        use_enum_values = True
    """Object where keys are shape families for which this permeability is valid. If missing,
    the variant is valid for all shapes
    
    Coefficients given by Magnetics in order to calculate the permeability of their cores
    """
    """Field with the coefficients used to calculate how much the permeability decreases with
    the H DC bias, as factor = a + b * pow(H, c)
    """
    magneticFieldDcBiasFactor: MagneticFieldDcBiasFactor
    """Field with the coefficients used to calculate how much the permeability decreases with
    the frequency, as factor = a + b * f + c * pow(f, 2) + d * pow(f, 3) + e * pow(f, 4)
    """
    frequencyFactor: Optional[FrequencyFactor] = None
    """Name of this method"""
    method: Optional[str] = None
    """Field with the coefficients used to calculate how much the permeability decreases with
    the temperature, as factor = a + b * T + c * pow(T, 2) + d * pow(T, 3) + e * pow(T, 4)
    """
    temperatureFactor: Optional[TemperatureFactor] = None



class PermeabilityPoint(BaseModel):
    class Config:  
        use_enum_values = True
    """data for describing one point of permebility"""
    """Permeability value"""
    value: float
    """Frequency of the Magnetic field, in Hz"""
    frequency: Optional[float] = None
    """DC bias in the magnetic field, in A/m"""
    magneticFieldDcBias: Optional[float] = None
    """magnetic flux density peak for the field value, in T"""
    magneticFluxDensityPeak: Optional[float] = None
    """The initial permeability of a magnetic material according to its manufacturer"""
    modifiers: Optional[Dict[str, MagneticsPermeabilityMethodData]] = None
    """temperature for the field value, in Celsius"""
    temperature: Optional[float] = None
    """tolerance for the field value"""
    tolerance: Optional[float] = None



class Permeabilities(BaseModel):
    class Config:  
        use_enum_values = True
    """The data regarding the relative permeability of a magnetic material"""
    amplitude: Optional[Union[PermeabilityPoint, List[PermeabilityPoint]]] = None
    initial: Union[PermeabilityPoint, List[PermeabilityPoint]]


class CoreMaterialType(Enum):
    """The type of a magnetic material"""
    commercial = "commercial"
    custom = "custom"



class VolumetricLossesPoint(BaseModel):
    class Config:  
        use_enum_values = True
    """data for describing the volumetric losses at a given point of magnetic flux density,
    frequency and temperature
    
    List of volumetric losses points
    """
    magneticFluxDensity: OperationPointExcitation
    """origin of the data"""
    origin: str
    """temperature value, in Celsius"""
    temperature: float
    """volumetric losses value, in W/m3"""
    value: float



class RoshenAdditionalCoefficients(BaseModel):
    class Config:  
        use_enum_values = True
    """List of coefficients for taking into account the excess losses and the dependencies of
    the resistivity
    """
    excessLossesCoefficient: float
    resistivityFrequencyCoefficient: float
    resistivityMagneticFluxDensityCoefficient: float
    resistivityOffset: float
    resistivityTemperatureCoefficient: float



class SteinmetzCoreLossesMethodRangeDatum(BaseModel):
    class Config:  
        use_enum_values = True
    """frequency power coefficient alpha"""
    alpha: float
    """magnetic flux density power coefficient beta"""
    beta: float
    """Proportional coefficient k"""
    k: float
    """Constant temperature coefficient ct0"""
    ct0: Optional[float] = None
    """Proportional negative temperature coefficient ct1"""
    ct1: Optional[float] = None
    """Square temperature coefficient ct2"""
    ct2: Optional[float] = None
    """maximum frequency for which the coefficients are valid, in Hz"""
    maximumFrequency: Optional[float] = None
    """minimum frequency for which the coefficients are valid, in Hz"""
    minimumFrequency: Optional[float] = None



class ResistivityPoint(BaseModel):
    class Config:  
        use_enum_values = True
    """data for describing one point of resistivity"""
    """Resistivity value, in Ohm * m"""
    value: float
    """temperature for the field value, in Celsius"""
    temperature: Optional[float] = None



class CoreLossesMethodData(BaseModel):
    class Config:  
        use_enum_values = True
    """Steinmetz coefficients for estimating volumetric losses in a given frequency range
    
    Roshen coefficients for estimating volumetric losses
    """
    """Name of this method"""
    method: str
    ranges: Optional[List[SteinmetzCoreLossesMethodRangeDatum]] = None
    """List of coefficients for taking into account the excess losses and the dependencies of
    the resistivity
    """
    coefficients: Optional[RoshenAdditionalCoefficients] = None
    """BH Cycle points where the magnetic flux density is 0"""
    coerciveForce: Optional[List[SaturationElement]] = None
    """List of reference volumetric losses used to estimate excess eddy current losses"""
    referenceVolumetricLosses: Optional[List[VolumetricLossesPoint]] = None
    """BH Cycle points where the magnetic field is 0"""
    remanence: Optional[List[SaturationElement]] = None
    """Resistivity value according to manufacturer"""
    resistivity: Optional[List[ResistivityPoint]] = None



class CoreMaterial(BaseModel):
    class Config:  
        use_enum_values = True
    """A material for the magnetic cores"""
    manufacturerInfo: ManufacturerInfo
    """The composition of a magnetic material"""
    materialComposition: MaterialComposition
    """The name of a magnetic material"""
    name: str
    """The data regarding the relative permeability of a magnetic material"""
    permeability: Permeabilities
    """BH Cycle points where a non-negligible increase in magnetic field produces a negligible
    increase of magnetic flux density
    """
    saturation: List[SaturationElement]
    """The type of a magnetic material"""
    type: CoreMaterialType
    """The data regarding the volumetric losses of a magnetic material"""
    volumetricLosses: Dict[str, List[Union[CoreLossesMethodData, List[VolumetricLossesPoint]]]]
    bhCycle: Optional[List[SaturationElement]] = None
    """The temperature at which this material losses all ferromagnetism"""
    curieTemperature: Optional[float] = None
    """The family of a magnetic material according to its manufacturer"""
    family: Optional[str] = None



class DimensionWithTolerance(BaseModel):
    class Config:  
        use_enum_values = True
    """The conducting diameter of the wire, in m
    
    The conducting height of the wire, in m
    
    The conducting thickness of the wire, in m
    
    The conducting width of the wire, in m
    
    The outer diameter of the wire, in m
    
    The outer height of the wire, in m
    
    The outer thickness of the wire, in m
    
    The outer width of the wire, in m
    
    A dimension of the wire, in m
    """
    """The maximum value of the dimension, in m"""
    maximum: Optional[float] = None
    """The minimum value of the dimension, in m"""
    minimum: Optional[float] = None
    """The nominal value of the dimension, in m"""
    nominal: Optional[float] = None


class CoreShapeFamily(Enum):
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
    t = "t"
    u = "u"
    ui = "ui"
    ur = "ur"
    ut = "ut"


class MagneticCircuit(Enum):
    """Describes if the magnetic circuit of the shape is open, and can be combined with others;
    or closed, and has to be used by itself
    """
    closed = "closed"
    open = "open"


class CoreShapeType(Enum):
    """The type of a magnetic shape
    
    The type of a bobbin
    """
    custom = "custom"
    standard = "standard"



class CoreShape(BaseModel):
    class Config:  
        use_enum_values = True
    """A shape for the magnetic cores"""
    """The family of a magnetic shape"""
    family: CoreShapeFamily
    """The type of a magnetic shape"""
    type: CoreShapeType
    """Alternative names of a magnetic shape"""
    aliases: Optional[List[str]] = None
    """The dimensions of a magnetic shape, keys must be as defined in EN 62317"""
    dimensions: Optional[Dict[str, Union[DimensionWithTolerance, float]]] = None
    """The subtype of the shape, in case there are more than one"""
    familySubtype: Optional[str] = None
    """Describes if the magnetic circuit of the shape is open, and can be combined with others;
    or closed, and has to be used by itself
    """
    magneticCircuit: Optional[MagneticCircuit] = None
    """The name of a magnetic shape"""
    name: Optional[str] = None


class CoreType(Enum):
    """The type of core"""
    closedshape = "closed shape"
    pieceandplate = "piece and plate"
    toroidal = "toroidal"
    twopieceset = "two-piece set"



class CoreFunctionalDescription(BaseModel):
    class Config:  
        use_enum_values = True
    """The data from the core based on its function, in a way that can be used by analytical
    models.
    """
    """The lists of gaps in the magnetic core"""
    gapping: List[CoreGap]
    material: Union[CoreMaterial, str]
    shape: Union[CoreShape, str]
    """The type of core"""
    type: CoreType
    """The number of stacked cores"""
    numberStacks: Optional[int] = None


class Composition(Enum):
    """The composition of a insulation material"""
    air = "air"
    bakelite = "bakelite"
    nylon = "nylon"
    paper = "paper"
    polyimide = "polyimide"
    polystyrene = "polystyrene"
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



class InsulationMaterial(BaseModel):
    class Config:  
        use_enum_values = True
    """A material for insulation"""
    dielectricStrength: List[DielectricStrengthElement]
    """The name of a insulation material"""
    name: str
    """The composition of a insulation material"""
    composition: Optional[Composition] = None
    """The manufacturer of the insulation material"""
    manufacturer: Optional[str] = None
    """The rating of the material"""
    rating: Optional[Rating] = None
    """The thermal conductivity of the insulation material, in W / m * K"""
    thermalConductivity: Optional[float] = None



class Piece(BaseModel):
    class Config:  
        use_enum_values = True
    """Data describing the machining applied to a piece"""
    """The coordinates of the start of the machining, referred to the top of the main column of
    the piece
    """
    coordinates: List[float]
    """Length of the machining"""
    length: float


class CoreGeometricalDescriptionElementType(Enum):
    """The type of piece
    
    The type of spacer
    """
    closed = "closed"
    halfset = "half set"
    plate = "plate"
    sheet = "sheet"
    spacer = "spacer"
    toroidal = "toroidal"



class CoreGeometricalDescriptionElement(BaseModel):
    class Config:  
        use_enum_values = True
    """The data from the core based on its geometrical description, in a way that can be used by
    CAD models.
    
    Data describing the a piece of a core
    
    Data describing the spacer used to separate cores in additive gaps
    """
    """The coordinates of the top of the piece, referred to the center of the main column
    
    The coordinates of the center of the gap, referred to the center of the main column
    """
    coordinates: List[float]
    material: Optional[Union[CoreMaterial, str]] = None
    shape: Optional[Union[CoreShape, str]] = None
    """The type of piece
    
    The type of spacer
    """
    type: CoreGeometricalDescriptionElementType
    """Material of the spacer"""
    insulationMaterial: Optional[Union[InsulationMaterial, str]] = None
    machining: Optional[List[Piece]] = None
    """The rotation of the top of the piece from its original state, referred to the center of
    the main column
    """
    rotation: Optional[List[float]] = None
    """Dimensions of the cube defining the spacer"""
    dimensions: Optional[List[float]] = None


class ColumnType(Enum):
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
    shape: ColumnShape
    """Name of the column"""
    type: ColumnType
    """Width of the column"""
    width: float



class EffectiveParameters(BaseModel):
    class Config:  
        use_enum_values = True
    """Effective data of the magnetic core"""
    """This is the equivalent section that the magnetic flux traverses, because the shape of the
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



class CoreProcessedDescription(BaseModel):
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



class MagneticCore(BaseModel):
    class Config:  
        use_enum_values = True
    """Data describing the magnetic core.
    
    The description of a magnetic core
    """
    """The data from the core based on its function, in a way that can be used by analytical
    models.
    """
    functionalDescription: CoreFunctionalDescription
    """List with data from the core based on its geometrical description, in a way that can be
    used by CAD models.
    """
    geometricalDescription: Optional[List[CoreGeometricalDescriptionElement]] = None
    manufacturerInfo: Optional[ManufacturerInfo] = None
    """The name of core"""
    name: Optional[str] = None
    """The data from the core after been processed, and ready to use by the analytical models"""
    processedDescription: Optional[CoreProcessedDescription] = None


class CoreBobbinFamily(Enum):
    """The family of a bobbin"""
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



class ProcessedData(BaseModel):
    class Config:  
        use_enum_values = True
    """TBD, add separators"""
    """The thicknes of the central column wall, where the wire is wound"""
    columnThickness: Optional[float] = None
    """The thicknes of the walls that hold the wire on both sides of the column"""
    wallThickness: Optional[float] = None



class CoreBobbin(BaseModel):
    class Config:  
        use_enum_values = True
    """A shape for the magnetic cores"""
    """The family of a bobbin"""
    family: CoreBobbinFamily
    """The type of a bobbin"""
    type: CoreShapeType
    """The dimensions of a bobbin, keys must be as defined in EN 62317"""
    dimensions: Optional[Dict[str, Union[DimensionWithTolerance, float]]] = None
    """The subtype of the shape, in case there are more than one"""
    familySubtype: Optional[str] = None
    manufacturerInfo: Optional[ManufacturerInfo] = None
    """The name of a bobbin, according to EN 62317"""
    name: Optional[str] = None
    """TBD, add separators"""
    processedData: Optional[ProcessedData] = None
    """The name of a bobbin that this bobbin belongs to"""
    shape: Optional[str] = None


class IsolationSide(Enum):
    """Tag to identify windings that are sharing the same ground"""
    denary = "denary"
    duodenary = "duodenary"
    nonary = "nonary"
    octonary = "octonary"
    primary = "primary"
    quaternary = "quaternary"
    quinary = "quinary"
    secondary = "secondary"
    senary = "senary"
    septenary = "septenary"
    tertiary = "tertiary"
    undenary = "undenary"


class InsulationWireCoatingType(Enum):
    """The type of the coating"""
    bare = "bare"
    enamelled = "enamelled"
    extruded = "extruded"
    insulated = "insulated"
    served = "served"
    taped = "taped"



class InsulationWireCoating(BaseModel):
    class Config:  
        use_enum_values = True
    """A coating for a wire"""
    material: Optional[Union[InsulationMaterial, str]] = None
    """The minimum voltage that causes a portion of an insulator to experience electrical
    breakdown and become electrically conductive, in V
    """
    breakdownVoltage: Optional[float] = None
    """The grade of the insulation around the wire"""
    grade: Optional[int] = None
    """The maximum thickness of the insulation around the wire, in m"""
    maximumThickness: Optional[float] = None
    """The number of layers of the insulation around the wire"""
    numberLayers: Optional[int] = None
    """The thickness of the layers of the insulation around the wire, in m"""
    thicknessLayers: Optional[float] = None
    """The type of the coating"""
    type: Optional[InsulationWireCoatingType] = None



class Resistivity(BaseModel):
    class Config:  
        use_enum_values = True
    """data for describing the resistivity of a wire"""
    """Temperature reference value, in Celsius"""
    referenceTemperature: float
    """Resistivity reference value, in Ohm * m"""
    referenceValue: float
    """Temperature coefficient value, alpha, in 1 / Celsius"""
    temperatureCoefficient: float



class ThermalConductivityElement(BaseModel):
    class Config:  
        use_enum_values = True
    """data for describing one point of thermal conductivity"""
    """Temperature for the field value, in Celsius"""
    temperature: float
    """Thermal conductivity value, in W / m * K"""
    value: float



class WireMaterial(BaseModel):
    class Config:  
        use_enum_values = True
    """A material for wire"""
    """The name of a wire material"""
    name: str
    """The permeability of a wire material"""
    permeability: float
    resistivity: Resistivity
    thermalConductivity: Optional[List[ThermalConductivityElement]] = None


class Standard(Enum):
    """The standard of wire"""
    IEC60317 = "IEC 60317"
    JISC3202 = "JIS C3202"
    NEMAMW1000C = "NEMA MW 1000C"


class WireSolidType(Enum):
    """The type of wire"""
    foil = "foil"
    rectangular = "rectangular"
    round = "round"



class WireSolid(BaseModel):
    class Config:  
        use_enum_values = True
    """The description of a solid magnet wire"""
    coating: Optional[Union[InsulationWireCoating, str]] = None
    material: Optional[Union[WireMaterial, str]] = None
    """The conducting diameter of the wire, in m"""
    conductingDiameter: Optional[DimensionWithTolerance] = None
    """The conducting height of the wire, in m"""
    conductingHeight: Optional[DimensionWithTolerance] = None
    """The conducting thickness of the wire, in m"""
    conductingThickness: Optional[DimensionWithTolerance] = None
    """The conducting width of the wire, in m"""
    conductingWidth: Optional[DimensionWithTolerance] = None
    manufacturerInfo: Optional[ManufacturerInfo] = None
    """The name of wire"""
    name: Optional[str] = None
    """The number of conductors in the wire"""
    numberConductors: Optional[float] = None
    """The outer diameter of the wire, in m"""
    outerDiameter: Optional[DimensionWithTolerance] = None
    """The outer height of the wire, in m"""
    outerHeight: Optional[DimensionWithTolerance] = None
    """The outer thickness of the wire, in m"""
    outerThickness: Optional[DimensionWithTolerance] = None
    """The outer width of the wire, in m"""
    outerWidth: Optional[DimensionWithTolerance] = None
    """The standard of wire"""
    standard: Optional[Standard] = None
    """The type of wire"""
    type: Optional[WireSolidType] = None



class WireS(BaseModel):
    class Config:  
        use_enum_values = True
    """The description of a solid magnet wire
    
    The description of a strand magnet wire
    """
    coating: Optional[Union[InsulationWireCoating, str]] = None
    material: Optional[Union[WireMaterial, str]] = None
    """The wire used as strands"""
    strand: Optional[Union[WireSolid, str]] = None
    """The conducting diameter of the wire, in m"""
    conductingDiameter: Optional[DimensionWithTolerance] = None
    """The conducting height of the wire, in m"""
    conductingHeight: Optional[DimensionWithTolerance] = None
    """The conducting thickness of the wire, in m"""
    conductingThickness: Optional[DimensionWithTolerance] = None
    """The conducting width of the wire, in m"""
    conductingWidth: Optional[DimensionWithTolerance] = None
    manufacturerInfo: Optional[ManufacturerInfo] = None
    """The name of wire"""
    name: Optional[str] = None
    """The number of conductors in the wire"""
    numberConductors: Optional[float] = None
    """The outer diameter of the wire, in m"""
    outerDiameter: Optional[DimensionWithTolerance] = None
    """The outer height of the wire, in m"""
    outerHeight: Optional[DimensionWithTolerance] = None
    """The outer thickness of the wire, in m"""
    outerThickness: Optional[DimensionWithTolerance] = None
    """The outer width of the wire, in m"""
    outerWidth: Optional[DimensionWithTolerance] = None
    """The standard of wire"""
    standard: Optional[Standard] = None
    """The type of wire"""
    type: Optional[str] = None



class WindingFunctionalDescription(BaseModel):
    class Config:  
        use_enum_values = True
    """Data describing one winding associated with a magnetic"""
    """Tag to identify windings that are sharing the same ground"""
    isolationSide: IsolationSide
    """Name given to the winding"""
    name: str
    """Number of parallels in winding"""
    numberParallels: int
    """Number of turns in winding"""
    numberTurns: int
    wire: Union[WireS, str]


class LayersOrientationEnum(Enum):
    """Way in which the layer is oriented inside the section
    
    Way in which the layers are oriented inside the section
    """
    horizontal = "horizontal"
    radial = "radial"
    vertical = "vertical"



class PartialWindingElement(BaseModel):
    class Config:  
        use_enum_values = True
    """Data describing one part of winding, described by a list with the proportion of each
    parallel in the winding that is contained here
    """
    """Name given to the partial winding"""
    name: str
    """Number of parallels in winding"""
    parallelsProportion: List[float]
    """The name of the winding that this part belongs to"""
    winding: str


class LayersDescriptionType(Enum):
    """Type of the layer"""
    insulation = "insulation"
    wiring = "wiring"



class LayersDescriptionElement(BaseModel):
    class Config:  
        use_enum_values = True
    """Data describing one layer in a magnetic"""
    """The coordinates of the center of the section, referred to the center of the main column"""
    coordinates: List[float]
    """Dimensions of the rectangle defining the section"""
    dimensions: List[float]
    """In case of insulating layer, the material used"""
    insulationMaterial: Optional[Union[InsulationMaterial, str]] = None
    """Name given to the layer"""
    name: str
    """Way in which the layer is oriented inside the section"""
    orientation: LayersOrientationEnum
    """List of partial windings in this section"""
    partialWindings: List[PartialWindingElement]
    """Type of the layer"""
    type: LayersDescriptionType
    """The name of the section that this layer belongs to"""
    section: Optional[str] = None



class SectionsDescriptionElement(BaseModel):
    class Config:  
        use_enum_values = True
    """Data describing one section in a magnetic"""
    """The coordinates of the center of the section, referred to the center of the main column"""
    coordinates: List[float]
    """Dimensions of the rectangle defining the section"""
    dimensions: List[float]
    """Way in which the layers are oriented inside the section"""
    layersOrientation: LayersOrientationEnum
    """Name given to the winding"""
    name: str
    """List of partial windings in this section"""
    partialWindings: List[PartialWindingElement]


class TurnsDescriptionOrientation(Enum):
    """Way in which the turn is wound"""
    clockwire = "clockwire"
    counterClockwise = "counterClockwise"



class TurnsDescriptionElement(BaseModel):
    class Config:  
        use_enum_values = True
    """Data describing one turn in a magnetic"""
    """The coordinates of the center of the section, referred to the center of the main column"""
    coordinates: List[float]
    """The length of the turn, referred from the center of its cross section, in m"""
    length: float
    """Name given to the turn"""
    name: str
    """The name of the parallel that this turn belongs to"""
    parallel: str
    """The name of the winding that this turn belongs to"""
    winding: str
    """The angle that the turn does, useful for partial turns, in degrees"""
    angle: Optional[float] = None
    """The name of the layer that this turn belongs to"""
    layer: Optional[str] = None
    """Way in which the turn is wound"""
    orientation: Optional[TurnsDescriptionOrientation] = None
    """The name of the section that this turn belongs to"""
    section: Optional[str] = None



class Winding(BaseModel):
    class Config:  
        use_enum_values = True
    """Data describing the winding
    
    The description of a magnetic winding
    """
    bobbin: Optional[Union[CoreBobbin, str]] = None
    """The data from the winding based on its function, in a way that can be used by analytical
    models of only Magnetism.
    """
    functionalDescription: List[WindingFunctionalDescription]
    """The data from the winding at the layer level, in a way that can be used by more advanced
    analytical and finite element models
    """
    layersDescription: Optional[List[LayersDescriptionElement]] = None
    """The data from the winding at the section level, in a way that can be used by more
    advanced analytical and finite element models
    """
    sectionsDescription: Optional[List[SectionsDescriptionElement]] = None
    """The data from the winding at the turn level, in a way that can be used by the most
    advanced analytical and finite element models
    """
    turnsDescription: Optional[List[TurnsDescriptionElement]] = None



class Magnetic(BaseModel):
    class Config:  
        use_enum_values = True
    """The description of a magnetic"""
    """Data describing the magnetic core."""
    core: MagneticCore
    """Data describing the winding"""
    winding: Winding



class Mas(BaseModel):
    class Config:  
        use_enum_values = True
    """All the data structure used in the Magnetic Agnostic Structure"""
    """The description of the inputs that can be used to design a Magnetic"""
    inputs: Inputs
    """The description of a magnetic"""
    magnetic: Magnetic
