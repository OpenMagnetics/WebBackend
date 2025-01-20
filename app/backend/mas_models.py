from pydantic import BaseModel
from typing import Optional, List, Dict, Union
from enum import Enum


class DimensionWithTolerance(BaseModel):
    class Config:  
        use_enum_values = True
    """Required values for the altitude
    
    Voltage RMS of the main supply to which this transformer is connected to.
    
    Required values for the magnetizing inductance
    
    Required values for the temperature that the magnetic can reach under operating
    
    The maximum thickness of the insulation around the wire, in m
    
    The conducting area of the wire, in m². Used for some rectangular shapes where the area
    is smaller than expected due to rounded corners
    
    The conducting diameter of the wire, in m
    
    The outer diameter of the wire, in m
    
    The conducting height of the wire, in m
    
    The conducting width of the wire, in m
    
    The outer height of the wire, in m
    
    The outer width of the wire, in m
    
    The radius of the edge, in case of rectangular wire, in m
    
    Heat capacity value according to manufacturer, in J/Kg/K
    
    Heat conductivity value according to manufacturer, in W/m/K
    
    Value of the leakage inductance between the primary and a secondary winding given by the
    position in the array
    
    Value of the magnetizing inductance
    
    Data a two dimensional matrix, created as an array of array, where the first coordinate
    in the X and the second the Y
    
    A dimension of with minimum, nominal, and maximum values
    """
    excludeMaximum: Optional[bool] = None
    """True is the maximum value must be excluded from the range"""
    excludeMinimum: Optional[bool] = None
    """True is the minimum value must be excluded from the range"""
    maximum: Optional[float] = None
    """The maximum value of the dimension"""
    minimum: Optional[float] = None
    """The minimum value of the dimension"""
    nominal: Optional[float] = None
    """The nominal value of the dimension"""


class CTI(Enum):
    """Required CTI"""
    GroupI = "Group I"
    GroupII = "Group II"
    GroupIIIA = "Group IIIA"
    GroupIIIB = "Group IIIB"


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


class InsulationStandards(Enum):
    IEC603351 = "IEC 60335-1"
    IEC606641 = "IEC 60664-1"
    IEC615581 = "IEC 61558-1"
    IEC623681 = "IEC 62368-1"


class InsulationRequirements(BaseModel):
    class Config:  
        use_enum_values = True
    altitude: Optional[DimensionWithTolerance] = None
    """Required values for the altitude"""
    cti: Optional[CTI] = None
    """Required CTI"""
    insulationType: Optional[InsulationType] = None
    """Required type of insulation"""
    mainSupplyVoltage: Optional[DimensionWithTolerance] = None
    """Voltage RMS of the main supply to which this transformer is connected to."""
    overvoltageCategory: Optional[OvervoltageCategory] = None
    """Required overvoltage category"""
    pollutionDegree: Optional[PollutionDegree] = None
    """Required pollution for the magnetic to work under"""
    standards: Optional[List[InsulationStandards]] = None
    """VList of standards that will be taken into account for insulation."""


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


class Market(Enum):
    """Market where the magnetic will end up being used"""
    Commercial = "Commercial"
    Industrial = "Industrial"
    Medical = "Medical"
    Military = "Military"
    Space = "Space"


class MaximumDimensions(BaseModel):
    class Config:  
        use_enum_values = True
    """Maximum dimensions, width, height, and depth, for the designed magnetic, in m"""
    depth: Optional[float] = None
    height: Optional[float] = None
    width: Optional[float] = None


class ConnectionType(Enum):
    """Type of the terminal"""
    FlyingLead = "Flying Lead"
    Pin = "Pin"
    SMT = "SMT"
    Screw = "Screw"


class Topology(Enum):
    """Topology that will use the magnetic"""
    ActiveClampForwardConverter = "Active Clamp Forward Converter"
    BoostConverter = "Boost Converter"
    BuckConverter = "Buck Converter"
    CukConverter = "Cuk Converter"
    FlybackConverter = "Flyback Converter"
    FullBridgeConverter = "Full-Bridge Converter"
    HalfBridgeConverter = "Half-Bridge Converter"
    InvertingBuckBoostConverter = "Inverting Buck-Boost Converter"
    PhaseShiftedFullBridgeConverter = "Phase-Shifted Full-Bridge Converter"
    PushPullConverter = "Push-Pull Converter"
    SEPIC = "SEPIC"
    SingleSwitchForwardConverter = "Single Switch Forward Converter"
    TwoSwitchFlybackConverter = "Two Switch Flyback Converter"
    TwoSwitchForwardConverter = "Two Switch Forward Converter"
    WeinbergConverter = "Weinberg Converter"
    ZetaConverter = "Zeta Converter"


class WiringTechnology(Enum):
    """Technology that must be used to create the wiring"""
    Deposition = "Deposition"
    Printed = "Printed"
    Wound = "Wound"


class DesignRequirements(BaseModel):
    class Config:  
        use_enum_values = True
    """Data describing the design requirements
    
    The list of requirement that must comply a given magnetic
    """
    magnetizingInductance: DimensionWithTolerance
    """Required values for the magnetizing inductance"""
    turnsRatios: List[DimensionWithTolerance]
    """Required turns ratios between primary and the rest of windings"""
    insulation: Optional[InsulationRequirements] = None
    isolationSides: Optional[List[IsolationSide]] = None
    """Isolation side where each winding is connected to."""
    leakageInductance: Optional[List[DimensionWithTolerance]] = None
    """Required values for the leakage inductance"""
    market: Optional[Market] = None
    """Market where the magnetic will end up being used"""
    maximumDimensions: Optional[MaximumDimensions] = None
    """Maximum dimensions, width, height, and depth, for the designed magnetic, in m"""
    maximumWeight: Optional[float] = None
    """Maximum weight for the designed magnetic, in Kg"""
    name: Optional[str] = None
    """A label that identifies these Design Requirements"""
    operatingTemperature: Optional[DimensionWithTolerance] = None
    """Required values for the temperature that the magnetic can reach under operating"""
    strayCapacitance: Optional[List[DimensionWithTolerance]] = None
    """Required values for the stray capacitance"""
    terminalType: Optional[List[ConnectionType]] = None
    """Type of the terminal that must be used, per winding"""
    topology: Optional[Topology] = None
    """Topology that will use the magnetic"""
    wiringTechnology: Optional[WiringTechnology] = None
    """Technology that must be used to create the wiring"""


class Cooling(BaseModel):
    class Config:  
        use_enum_values = True
    """Relative Humidity of the ambient where the magnetic will operate
    
    Data describing a natural convection cooling
    
    Data describing a forced convection cooling
    
    Data describing a heatsink cooling
    
    Data describing a cold plate cooling
    """
    fluid: Optional[str] = None
    """Name of the fluid used"""
    temperature: Optional[float] = None
    """Temperature of the fluid. To be used only if different from ambient temperature"""
    flowDiameter: Optional[float] = None
    """Diameter of the fluid flow, normally defined as a fan diameter"""
    velocity: Optional[List[float]] = None
    dimensions: Optional[List[float]] = None
    """Dimensions of the cube defining the heatsink
    
    Dimensions of the cube defining the cold plate
    """
    interfaceThermalResistance: Optional[float] = None
    """Bulk thermal resistance of the thermal interface used to connect the device to the
    heatsink, in W/mK
    
    Bulk thermal resistance of the thermal interface used to connect the device to the cold
    plate, in W/mK
    """
    interfaceThickness: Optional[float] = None
    """Thickness of the thermal interface used to connect the device to the heatsink, in m
    
    Thickness of the thermal interface used to connect the device to the cold plate, in m
    """
    thermalResistance: Optional[float] = None
    """Bulk thermal resistance of the heat sink, in W/K
    
    Bulk thermal resistance of the cold plate, in W/K
    """
    maximumTemperature: Optional[float] = None
    """Maximum temperature of the cold plate"""


class OperatingConditions(BaseModel):
    class Config:  
        use_enum_values = True
    """The description of a magnetic operating conditions"""
    ambientTemperature: float
    """Temperature of the ambient where the magnetic will operate"""
    ambientRelativeHumidity: Optional[float] = None
    """Relative Humidity of the ambient where the magnetic will operate"""
    cooling: Optional[Cooling] = None
    """Relative Humidity of the ambient where the magnetic will operate"""
    name: Optional[str] = None
    """A label that identifies this Operating Conditions"""


class Harmonics(BaseModel):
    class Config:  
        use_enum_values = True
    """Data containing the harmonics of the waveform, defined by a list of amplitudes and a list
    of frequencies
    """
    amplitudes: List[float]
    """List of amplitudes of the harmonics that compose the waveform"""
    frequencies: List[float]
    """List of frequencies of the harmonics that compose the waveform"""


class WaveformLabel(Enum):
    """Label of the waveform, if applicable. Used for common waveforms"""
    BipolarRectangular = "Bipolar Rectangular"
    BipolarTriangular = "Bipolar Triangular"
    Custom = "Custom"
    FlybackPrimary = "Flyback Primary"
    FlybackSecondary = "Flyback Secondary"
    Rectangular = "Rectangular"
    Sinusoidal = "Sinusoidal"
    Triangular = "Triangular"
    UnipolarRectangular = "Unipolar Rectangular"
    UnipolarTriangular = "Unipolar Triangular"


class Processed(BaseModel):
    class Config:  
        use_enum_values = True
    label: WaveformLabel
    """Label of the waveform, if applicable. Used for common waveforms"""
    offset: float
    """The offset value of the waveform, referred to 0"""
    acEffectiveFrequency: Optional[float] = None
    """The effective frequency value of the AC component of the waveform, according to
    https://sci-hub.wf/https://ieeexplore.ieee.org/document/750181, Appendix C
    """
    average: Optional[float] = None
    """The average value of the waveform, referred to 0"""
    dutyCycle: Optional[float] = None
    """The duty cycle of the waveform, if applicable"""
    effectiveFrequency: Optional[float] = None
    """The effective frequency value of the waveform, according to
    https://sci-hub.wf/https://ieeexplore.ieee.org/document/750181, Appendix C
    """
    peak: Optional[float] = None
    """The maximum positive value of the waveform"""
    peakToPeak: Optional[float] = None
    """The peak to peak value of the waveform"""
    rms: Optional[float] = None
    """The RMS value of the waveform"""
    thd: Optional[float] = None
    """The Total Harmonic Distortion of the waveform, according to
    https://en.wikipedia.org/wiki/Total_harmonic_distortion
    """


class Waveform(BaseModel):
    class Config:  
        use_enum_values = True
    """Data containing the points that define an arbitrary waveform with equidistant points
    
    Data containing the points that define an arbitrary waveform with non-equidistant points
    paired with their time in the period
    """
    data: List[float]
    """List of values that compose the waveform, at equidistant times form each other"""
    numberPeriods: Optional[int] = None
    """The number of periods covered by the data"""
    ancillaryLabel: Optional[str] = None
    time: Optional[List[float]] = None


class SignalDescriptor(BaseModel):
    class Config:  
        use_enum_values = True
    """Excitation of the B field that produced the core losses
    
    Structure definining one electromagnetic parameters: current, voltage, magnetic flux
    density
    """
    harmonics: Optional[Harmonics] = None
    """Data containing the harmonics of the waveform, defined by a list of amplitudes and a list
    of frequencies
    """
    processed: Optional[Processed] = None
    waveform: Optional[Waveform] = None


class OperatingPointExcitation(BaseModel):
    class Config:  
        use_enum_values = True
    """Data describing the excitation of the winding
    
    The description of a magnetic operating point
    """
    frequency: float
    """Frequency of the waveform, common for all electromagnetic parameters, in Hz"""
    current: Optional[SignalDescriptor] = None
    magneticFieldStrength: Optional[SignalDescriptor] = None
    magneticFluxDensity: Optional[SignalDescriptor] = None
    magnetizingCurrent: Optional[SignalDescriptor] = None
    name: Optional[str] = None
    """A label that identifies this Operating Point"""
    voltage: Optional[SignalDescriptor] = None


class OperatingPoint(BaseModel):
    class Config:  
        use_enum_values = True
    """Data describing one operating point, including the operating conditions and the
    excitations for all ports
    
    Excitation of the current per winding that produced the winding losses
    """
    conditions: OperatingConditions
    excitationsPerWinding: List[OperatingPointExcitation]
    name: Optional[str] = None
    """Name describing this operating point"""


class Inputs(BaseModel):
    class Config:  
        use_enum_values = True
    """The description of the inputs that can be used to design a Magnetic"""
    designRequirements: DesignRequirements
    """Data describing the design requirements"""
    operatingPoints: List[OperatingPoint]
    """Data describing the operating points"""


class DistributorInfo(BaseModel):
    class Config:  
        use_enum_values = True
    """Data from the distributor for a given part"""
    name: str
    """The name of the distributor of the part"""
    quantity: float
    """The number of individual pieces available in the distributor"""
    reference: str
    """The distributor's reference of this part"""
    cost: Optional[float] = None
    """The distributor's price for this part"""
    country: Optional[str] = None
    """The country of the distributor of the part"""
    distributedArea: Optional[str] = None
    """The area where the distributor doistributes"""
    email: Optional[str] = None
    """The distributor's email"""
    link: Optional[str] = None
    """The distributor's link"""
    phone: Optional[str] = None
    """The distributor's phone"""
    updatedAt: Optional[str] = None
    """The date that this information was updated"""


class PinWIndingConnection(BaseModel):
    class Config:  
        use_enum_values = True
    pin: Optional[str] = None
    """The name of the connected pin"""
    winding: Optional[str] = None
    """The name of the connected winding"""


class BobbinFamily(Enum):
    """The family of a bobbin"""
    e = "e"
    ec = "ec"
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


class PinShape(Enum):
    """The shape of the pin"""
    irregular = "irregular"
    rectangular = "rectangular"
    round = "round"


class PinDescriptionType(Enum):
    """Type of pin"""
    smd = "smd"
    tht = "tht"


class Pin(BaseModel):
    class Config:  
        use_enum_values = True
    """Data describing one pin in a bobbin"""
    dimensions: List[float]
    """Dimensions of the rectangle defining the pin"""
    shape: PinShape
    """The shape of the pin"""
    type: PinDescriptionType
    """Type of pin"""
    coordinates: Optional[List[float]] = None
    """The coordinates of the center of the pin, referred to the center of the main column"""
    name: Optional[str] = None
    """Name given to the pin"""
    rotation: Optional[List[float]] = None
    """The rotation of the pin, default is vertical"""


class Pinout(BaseModel):
    class Config:  
        use_enum_values = True
    """Data describing the pinout of a bobbin"""
    numberPins: int
    """The number of pins"""
    pinDescription: Pin
    pitch: List[float]
    """The distance between pins, per row, by pin order"""
    rowDistance: float
    """The distance between a row of pins and the center of the bobbin"""
    centralPitch: Optional[float] = None
    """The distance between central pins"""
    numberPinsPerRow: Optional[List[int]] = None
    """List of pins per row"""
    numberRows: Optional[int] = None
    """The number of rows of a bobbin, typically 2"""


class FunctionalDescriptionType(Enum):
    """The type of a bobbin
    
    The type of a magnetic shape
    """
    custom = "custom"
    standard = "standard"


class BobbinFunctionalDescription(BaseModel):
    class Config:  
        use_enum_values = True
    """The data from the bobbin based on its function, in a way that can be used by analytical
    models.
    """
    dimensions: Dict[str, Union[DimensionWithTolerance, float]]
    """The dimensions of a bobbin, keys must be as defined in EN 62317"""
    family: BobbinFamily
    """The family of a bobbin"""
    shape: str
    """The name of a bobbin that this bobbin belongs to"""
    type: FunctionalDescriptionType
    """The type of a bobbin"""
    connections: Optional[List[PinWIndingConnection]] = None
    """List of connections between windings and pins"""
    familySubtype: Optional[str] = None
    """The subtype of the shape, in case there are more than one"""
    pinout: Optional[Pinout] = None


class Status(Enum):
    """The production status of a part according to its manufacturer"""
    obsolete = "obsolete"
    production = "production"
    prototype = "prototype"


class ManufacturerInfo(BaseModel):
    class Config:  
        use_enum_values = True
    """Data from the manufacturer for a given part"""
    name: str
    """The name of the manufacturer of the part"""
    cost: Optional[str] = None
    """The manufacturer's price for this part"""
    datasheetUrl: Optional[str] = None
    """The manufacturer's URL to the datasheet of the product"""
    family: Optional[str] = None
    """The family of a magnetic, as defined by the manufacturer"""
    orderCode: Optional[str] = None
    """The manufacturer's order code of this part"""
    reference: Optional[str] = None
    """The manufacturer's reference of this part"""
    status: Optional[Status] = None
    """The production status of a part according to its manufacturer"""


class ColumnShape(Enum):
    """Shape of the column, also used for gaps"""
    irregular = "irregular"
    oblong = "oblong"
    rectangular = "rectangular"
    round = "round"


class WindingOrientation(Enum):
    """Way in which the sections are oriented inside the winding window
    
    Way in which the layer is oriented inside the section
    
    Way in which the layers are oriented inside the section
    """
    contiguous = "contiguous"
    overlapping = "overlapping"


class WindingWindowShape(Enum):
    rectangular = "rectangular"
    round = "round"


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
    area: Optional[float] = None
    """Area of the winding window"""
    coordinates: Optional[List[float]] = None
    """The coordinates of the center of the winding window, referred to the center of the main
    column. In the case of half-sets, the center will be in the top point, where it would
    join another half-set
    
    The coordinates of the point of the winding window where the middle height touches the
    main column, referred to the center of the main column. In the case of half-sets, the
    center will be in the top point, where it would join another half-set
    """
    height: Optional[float] = None
    """Vertical height of the winding window"""
    sectionsOrientation: Optional[WindingOrientation] = None
    """Way in which the sections are oriented inside the winding window"""
    shape: Optional[WindingWindowShape] = None
    """Shape of the winding window"""
    width: Optional[float] = None
    """Horizontal width of the winding window"""
    angle: Optional[float] = None
    """Total angle of the window"""
    radialHeight: Optional[float] = None
    """Radial height of the winding window"""


class CoreBobbinProcessedDescription(BaseModel):
    class Config:  
        use_enum_values = True
    columnDepth: float
    """The depth of the central column wall, including thickness, in the z axis"""
    columnShape: ColumnShape
    columnThickness: float
    """The thicknes of the central column wall, where the wire is wound, in the X axis"""
    wallThickness: float
    """The thicknes of the walls that hold the wire on both sides of the column"""
    windingWindows: List[WindingWindowElement]
    """List of winding windows, all elements in the list must be of the same type"""
    columnWidth: Optional[float] = None
    """The width of the central column wall, including thickness, in the x axis"""
    coordinates: Optional[List[float]] = None
    """The coordinates of the center of the bobbin central wall, whre the wires are wound,
    referred to the center of the main column.
    """
    pins: Optional[List[Pin]] = None
    """List of pins, geometrically defining how and where it is"""


class Bobbin(BaseModel):
    class Config:  
        use_enum_values = True
    """The description of a bobbin"""
    distributorsInfo: Optional[List[DistributorInfo]] = None
    """The lists of distributors of the magnetic bobbin"""
    functionalDescription: Optional[BobbinFunctionalDescription] = None
    """The data from the bobbin based on its function, in a way that can be used by analytical
    models.
    """
    manufacturerInfo: Optional[ManufacturerInfo] = None
    name: Optional[str] = None
    """The name of bobbin"""
    processedDescription: Optional[CoreBobbinProcessedDescription] = None


class ConnectionElement(BaseModel):
    class Config:  
        use_enum_values = True
    """Data describing the connection of the a wire"""
    length: Optional[float] = None
    """Length of the connection, counted from the exit of the last turn until the terminal, in m"""
    metric: Optional[int] = None
    """Metric of the terminal, if applicable"""
    pinName: Optional[str] = None
    """Name of the pin where it is connected, if applicable"""
    type: Optional[ConnectionType] = None


class DielectricStrengthElement(BaseModel):
    class Config:  
        use_enum_values = True
    """data for describing one point of dieletric strength"""
    value: float
    """Dieletric strength value, in V / m"""
    humidity: Optional[float] = None
    """Humidity for the field value, in proportion over 1"""
    temperature: Optional[float] = None
    """Temperature for the field value, in Celsius"""
    thickness: Optional[float] = None
    """Thickness of the material"""


class ResistivityPoint(BaseModel):
    class Config:  
        use_enum_values = True
    """data for describing one point of resistivity"""
    value: float
    """Resistivity value, in Ohm * m"""
    temperature: Optional[float] = None
    """temperature for the field value, in Celsius"""


class InsulationMaterial(BaseModel):
    class Config:  
        use_enum_values = True
    """A material for insulation"""
    dielectricStrength: List[DielectricStrengthElement]
    name: str
    """The name of a insulation material"""
    aliases: Optional[List[str]] = None
    """Alternative names of the material"""
    composition: Optional[str] = None
    """The composition of a insulation material"""
    dielectricConstant: Optional[float] = None
    """The dielectric constant of the insulation material"""
    manufacturer: Optional[str] = None
    """The manufacturer of the insulation material"""
    meltingPoint: Optional[float] = None
    """The melting temperature of the insulation material, in Celsius"""
    resistivity: Optional[List[ResistivityPoint]] = None
    """Resistivity value according to manufacturer"""
    specificHeat: Optional[float] = None
    """The specific heat of the insulation material, in J / (Kg * K)"""
    temperatureClass: Optional[float] = None
    """The temperature class of the insulation material, in Celsius"""
    thermalConductivity: Optional[float] = None
    """The thermal conductivity of the insulation material, in W / (m * K)"""


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
    breakdownVoltage: Optional[float] = None
    """The minimum voltage that causes a portion of an insulator to experience electrical
    breakdown and become electrically conductive, in V
    """
    grade: Optional[int] = None
    """The grade of the insulation around the wire"""
    material: Optional[Union[InsulationMaterial, str]] = None
    numberLayers: Optional[int] = None
    """The number of layers of the insulation around the wire"""
    temperatureRating: Optional[float] = None
    """The maximum temperature that the wire coating can withstand"""
    thickness: Optional[DimensionWithTolerance] = None
    """The maximum thickness of the insulation around the wire, in m"""
    thicknessLayers: Optional[float] = None
    """The thickness of the layers of the insulation around the wire, in m"""
    type: Optional[InsulationWireCoatingType] = None
    """The type of the coating"""


class Resistivity(BaseModel):
    class Config:  
        use_enum_values = True
    """data for describing the resistivity of a wire"""
    referenceTemperature: float
    """Temperature reference value, in Celsius"""
    referenceValue: float
    """Resistivity reference value, in Ohm * m"""
    temperatureCoefficient: float
    """Temperature coefficient value, alpha, in 1 / Celsius"""


class ThermalConductivityElement(BaseModel):
    class Config:  
        use_enum_values = True
    """data for describing one point of thermal conductivity"""
    temperature: float
    """Temperature for the field value, in Celsius"""
    value: float
    """Thermal conductivity value, in W / m * K"""


class WireMaterial(BaseModel):
    class Config:  
        use_enum_values = True
    """A material for wire"""
    name: str
    """The name of a wire material"""
    permeability: float
    """The permeability of a wire material"""
    resistivity: Resistivity
    thermalConductivity: Optional[List[ThermalConductivityElement]] = None


class WireStandard(Enum):
    """The standard of wire"""
    IEC60317 = "IEC 60317"
    JISC3202 = "JIS C3202"
    NEMAMW1000C = "NEMA MW 1000 C"


class WireType(Enum):
    """The type of wire"""
    foil = "foil"
    litz = "litz"
    rectangular = "rectangular"
    round = "round"


class WireRound(BaseModel):
    class Config:  
        use_enum_values = True
    """The description of a solid round magnet wire
    
    The description of a basic magnet wire
    """
    conductingDiameter: DimensionWithTolerance
    """The conducting diameter of the wire, in m"""
    type: WireType
    material: Optional[Union[WireMaterial, str]] = None
    outerDiameter: Optional[DimensionWithTolerance] = None
    """The outer diameter of the wire, in m"""
    coating: Optional[Union[InsulationWireCoating, str]] = None
    conductingArea: Optional[DimensionWithTolerance] = None
    """The conducting area of the wire, in m². Used for some rectangular shapes where the area
    is smaller than expected due to rounded corners
    """
    manufacturerInfo: Optional[ManufacturerInfo] = None
    name: Optional[str] = None
    """The name of wire"""
    numberConductors: Optional[int] = None
    """The number of conductors in the wire"""
    standard: Optional[WireStandard] = None
    """The standard of wire"""
    standardName: Optional[str] = None
    """Name according to the standard of wire"""


class Wire(BaseModel):
    class Config:  
        use_enum_values = True
    """The description of a solid round magnet wire
    
    The description of a basic magnet wire
    
    The description of a solid foil magnet wire
    
    The description of a solid rectangular magnet wire
    
    The description of a stranded litz magnet wire
    """
    type: WireType
    conductingDiameter: Optional[DimensionWithTolerance] = None
    """The conducting diameter of the wire, in m"""
    material: Optional[Union[WireMaterial, str]] = None
    outerDiameter: Optional[DimensionWithTolerance] = None
    """The outer diameter of the wire, in m"""
    coating: Optional[Union[InsulationWireCoating, str]] = None
    conductingArea: Optional[DimensionWithTolerance] = None
    """The conducting area of the wire, in m². Used for some rectangular shapes where the area
    is smaller than expected due to rounded corners
    """
    manufacturerInfo: Optional[ManufacturerInfo] = None
    name: Optional[str] = None
    """The name of wire"""
    numberConductors: Optional[int] = None
    """The number of conductors in the wire"""
    standard: Optional[WireStandard] = None
    """The standard of wire"""
    standardName: Optional[str] = None
    """Name according to the standard of wire"""
    conductingHeight: Optional[DimensionWithTolerance] = None
    """The conducting height of the wire, in m"""
    conductingWidth: Optional[DimensionWithTolerance] = None
    """The conducting width of the wire, in m"""
    outerHeight: Optional[DimensionWithTolerance] = None
    """The outer height of the wire, in m"""
    outerWidth: Optional[DimensionWithTolerance] = None
    """The outer width of the wire, in m"""
    edgeRadius: Optional[DimensionWithTolerance] = None
    """The radius of the edge, in case of rectangular wire, in m"""
    strand: Optional[Union[WireRound, str]] = None
    """The wire used as strands"""


class CoilFunctionalDescription(BaseModel):
    class Config:  
        use_enum_values = True
    """Data describing one winding associated with a magnetic"""
    isolationSide: IsolationSide
    name: str
    """Name given to the winding"""
    numberParallels: int
    """Number of parallels in winding"""
    numberTurns: int
    """Number of turns in winding"""
    wire: Union[Wire, str]
    connections: Optional[List[ConnectionElement]] = None
    """Array on elements, representing the all the pins this winding is connected to"""


class CoordinateSystem(Enum):
    """System in which dimension and coordinates are in"""
    cartesian = "cartesian"
    polar = "polar"


class PartialWinding(BaseModel):
    class Config:  
        use_enum_values = True
    """Data describing one part of winding, described by a list with the proportion of each
    parallel in the winding that is contained here
    """
    parallelsProportion: List[float]
    """Number of parallels in winding"""
    winding: str
    """The name of the winding that this part belongs to"""
    connections: Optional[List[ConnectionElement]] = None
    """Array on two elements, representing the input and output connection for this partial
    winding
    """


class CoilAlignment(Enum):
    """Way in which the turns are aligned inside the layer
    
    Way in which the layers are aligned inside the section
    """
    centered = "centered"
    innerortop = "inner or top"
    outerorbottom = "outer or bottom"
    spread = "spread"


class ElectricalType(Enum):
    """Type of the layer"""
    conduction = "conduction"
    insulation = "insulation"
    shielding = "shielding"


class WindingStyle(Enum):
    """Defines if the layer is wound by consecutive turns or parallels
    
    Defines if the section is wound by consecutive turns or parallels
    """
    windByConsecutiveParallels = "windByConsecutiveParallels"
    windByConsecutiveTurns = "windByConsecutiveTurns"


class Layer(BaseModel):
    class Config:  
        use_enum_values = True
    """Data describing one layer in a magnetic"""
    coordinates: List[float]
    """The coordinates of the center of the layer, referred to the center of the main column"""
    dimensions: List[float]
    """Dimensions of the rectangle defining the layer"""
    name: str
    """Name given to the layer"""
    orientation: WindingOrientation
    """Way in which the layer is oriented inside the section"""
    partialWindings: List[PartialWinding]
    """List of partial windings in this layer"""
    type: ElectricalType
    """Type of the layer"""
    additionalCoordinates: Optional[List[List[float]]] = None
    """List of additional coordinates of the center of the layer, referred to the center of the
    main column, in case the layer is not symmetrical, as in toroids
    """
    coordinateSystem: Optional[CoordinateSystem] = None
    """System in which dimension and coordinates are in"""
    fillingFactor: Optional[float] = None
    """How much space in this layer is used by wires compared to the total"""
    insulationMaterial: Optional[Union[InsulationMaterial, str]] = None
    """In case of insulating layer, the material used"""
    section: Optional[str] = None
    """The name of the section that this layer belongs to"""
    turnsAlignment: Optional[CoilAlignment] = None
    """Way in which the turns are aligned inside the layer"""
    windingStyle: Optional[WindingStyle] = None
    """Defines if the layer is wound by consecutive turns or parallels"""


class Section(BaseModel):
    class Config:  
        use_enum_values = True
    """Data describing one section in a magnetic"""
    coordinates: List[float]
    """The coordinates of the center of the section, referred to the center of the main column"""
    dimensions: List[float]
    """Dimensions of the rectangle defining the section"""
    layersOrientation: WindingOrientation
    """Way in which the layers are oriented inside the section"""
    name: str
    """Name given to the winding"""
    partialWindings: List[PartialWinding]
    """List of partial windings in this section"""
    type: ElectricalType
    """Type of the layer"""
    coordinateSystem: Optional[CoordinateSystem] = None
    """System in which dimension and coordinates are in"""
    fillingFactor: Optional[float] = None
    """How much space in this section is used by wires compared to the total"""
    layersAlignment: Optional[CoilAlignment] = None
    """Way in which the layers are aligned inside the section"""
    margin: Optional[List[float]] = None
    """Defines the distance in extremes of the section that is reserved to be filled with margin
    tape. It is an array os two elements from inner or top, to outer or bottom
    """
    windingStyle: Optional[WindingStyle] = None
    """Defines if the section is wound by consecutive turns or parallels"""


class TurnOrientation(Enum):
    """Way in which the turn is wound"""
    clockwise = "clockwise"
    counterClockwise = "counterClockwise"


class Turn(BaseModel):
    class Config:  
        use_enum_values = True
    """Data describing one turn in a magnetic"""
    coordinates: List[float]
    """The coordinates of the center of the turn, referred to the center of the main column"""
    length: float
    """The length of the turn, referred from the center of its cross section, in m"""
    name: str
    """Name given to the turn"""
    parallel: int
    """The index of the parallel that this turn belongs to"""
    winding: str
    """The name of the winding that this turn belongs to"""
    additionalCoordinates: Optional[List[List[float]]] = None
    """List of additional coordinates of the center of the turn, referred to the center of the
    main column, in case the turn is not symmetrical, as in toroids
    """
    angle: Optional[float] = None
    """The angle that the turn does, useful for partial turns, in degrees"""
    coordinateSystem: Optional[CoordinateSystem] = None
    """System in which dimension and coordinates are in"""
    dimensions: Optional[List[float]] = None
    """Dimensions of the rectangle defining the turn"""
    layer: Optional[str] = None
    """The name of the layer that this turn belongs to"""
    orientation: Optional[TurnOrientation] = None
    """Way in which the turn is wound"""
    rotation: Optional[float] = None
    """Rotation of the rectangle defining the turn, in degrees"""
    section: Optional[str] = None
    """The name of the section that this turn belongs to"""


class Coil(BaseModel):
    class Config:  
        use_enum_values = True
    """Data describing the coil
    
    The description of a magnetic coil
    """
    bobbin: Union[Bobbin, str]
    functionalDescription: List[CoilFunctionalDescription]
    """The data from the coil based on its function, in a way that can be used by analytical
    models of only Magnetism.
    """
    layersDescription: Optional[List[Layer]] = None
    """The data from the coil at the layer level, in a way that can be used by more advanced
    analytical and finite element models
    """
    sectionsDescription: Optional[List[Section]] = None
    """The data from the coil at the section level, in a way that can be used by more advanced
    analytical and finite element models
    """
    turnsDescription: Optional[List[Turn]] = None
    """The data from the coil at the turn level, in a way that can be used by the most advanced
    analytical and finite element models
    """


class Coating(Enum):
    """The coating of the core"""
    epoxy = "epoxy"
    parylene = "parylene"


class GapType(Enum):
    """The type of a gap"""
    additive = "additive"
    residual = "residual"
    subtractive = "subtractive"


class CoreGap(BaseModel):
    class Config:  
        use_enum_values = True
    """A gap for the magnetic cores"""
    length: float
    """The length of the gap"""
    type: GapType
    """The type of a gap"""
    area: Optional[float] = None
    """Geometrical area of the gap"""
    coordinates: Optional[List[float]] = None
    """The coordinates of the center of the gap, referred to the center of the main column"""
    distanceClosestNormalSurface: Optional[float] = None
    """The distance where the closest perpendicular surface is. This usually is half the winding
    height
    """
    distanceClosestParallelSurface: Optional[float] = None
    """The distance where the closest parallel surface is. This usually is the opposite side of
    the winnding window
    """
    sectionDimensions: Optional[List[float]] = None
    """Dimension of the section normal to the magnetic flux"""
    shape: Optional[ColumnShape] = None


class SaturationElement(BaseModel):
    class Config:  
        use_enum_values = True
    """data for describing one point of the BH cycle"""
    magneticField: float
    """magnetic field value, in A/m"""
    magneticFluxDensity: float
    """magnetic flux density value, in T"""
    temperature: float
    """temperature for the field value, in Celsius"""


class MaterialEnum(Enum):
    """The composition of a magnetic material"""

    amorphous = "amorphous"
    electricalSteel = "electricalSteel"
    ferrite = "ferrite"
    nanocrystalline = "nanocrystalline"
    powder = "powder"


class MaterialCompositionEnum(Enum):
    """The composition of a magnetic material"""

    FeMo = "FeMo"
    FeNi = "FeNi"
    FeNiMo = "FeNiMo"
    FeSi = "FeSi"
    FeSiAl = "FeSiAl"
    Iron = "Iron"
    MgZn = "MgZn"
    MnZn = "MnZn"
    NiZn = "NiZn"
    Proprietary = "Proprietary"


class FrequencyFactor(BaseModel):
    class Config:  
        use_enum_values = True
    """Field with the coefficients used to calculate how much the permeability decreases with
    the frequency, as factor = a + b * f + c * pow(f, 2) + d * pow(f, 3) + e * pow(f, 4)
    
    Field with the coefficients used to calculate how much the permeability decreases with
    the frequency, as factor = 1 / (a + b * pow(f, c) ) + d
    """
    a: float
    b: float
    c: float
    d: float
    e: Optional[float] = None


class MagneticFieldDcBiasFactor(BaseModel):
    class Config:  
        use_enum_values = True
    """Field with the coefficients used to calculate how much the permeability decreases with
    the H DC bias, as factor = a + b * pow(H, c)
    
    Field with the coefficients used to calculate how much the permeability decreases with
    the H DC bias, as factor = a + b * pow(H, c) + d
    """
    a: float
    b: float
    c: float
    d: Optional[float] = None


class MagneticFluxDensityFactor(BaseModel):
    class Config:  
        use_enum_values = True
    """Field with the coefficients used to calculate how much the permeability decreases with
    the B field, as factor = = 1 / ( 1 / ( a + b * pow(B,c)) + 1 / (d * pow(B, e) ) + 1 / f )
    """
    a: float
    b: float
    c: float
    d: float
    e: float
    f: float


class InitialPermeabilitModifierMethod(Enum):
    magnetics = "magnetics"
    micrometals = "micrometals"


class TemperatureFactor(BaseModel):
    class Config:  
        use_enum_values = True
    """Field with the coefficients used to calculate how much the permeability decreases with
    the temperature, as factor = a + b * T + c * pow(T, 2) + d * pow(T, 3) + e * pow(T, 4)
    
    Field with the coefficients used to calculate how much the permeability decreases with
    the temperature, as either factor = a * (T -20) * 0.0001 or factor = (a + c * T + e *
    pow(T, 2)) / (1 + b * T + d * pow(T, 2))
    """
    a: float
    b: Optional[float] = None
    c: Optional[float] = None
    d: Optional[float] = None
    e: Optional[float] = None


class InitialPermeabilitModifier(BaseModel):
    class Config:  
        use_enum_values = True
    """Object where keys are shape families for which this permeability is valid. If missing,
    the variant is valid for all shapes
    
    Coefficients given by Magnetics in order to calculate the permeability of their cores
    
    Coefficients given by Micrometals in order to calculate the permeability of their cores
    """
    magneticFieldDcBiasFactor: MagneticFieldDcBiasFactor
    """Field with the coefficients used to calculate how much the permeability decreases with
    the H DC bias, as factor = a + b * pow(H, c)
    
    Field with the coefficients used to calculate how much the permeability decreases with
    the H DC bias, as factor = a + b * pow(H, c) + d
    """
    frequencyFactor: Optional[FrequencyFactor] = None
    """Field with the coefficients used to calculate how much the permeability decreases with
    the frequency, as factor = a + b * f + c * pow(f, 2) + d * pow(f, 3) + e * pow(f, 4)
    
    Field with the coefficients used to calculate how much the permeability decreases with
    the frequency, as factor = 1 / (a + b * pow(f, c) ) + d
    """
    method: Optional[InitialPermeabilitModifierMethod] = None
    """Name of this method"""
    temperatureFactor: Optional[TemperatureFactor] = None
    """Field with the coefficients used to calculate how much the permeability decreases with
    the temperature, as factor = a + b * T + c * pow(T, 2) + d * pow(T, 3) + e * pow(T, 4)
    
    Field with the coefficients used to calculate how much the permeability decreases with
    the temperature, as either factor = a * (T -20) * 0.0001 or factor = (a + c * T + e *
    pow(T, 2)) / (1 + b * T + d * pow(T, 2))
    """
    magneticFluxDensityFactor: Optional[MagneticFluxDensityFactor] = None
    """Field with the coefficients used to calculate how much the permeability decreases with
    the B field, as factor = = 1 / ( 1 / ( a + b * pow(B,c)) + 1 / (d * pow(B, e) ) + 1 / f )
    """


class PermeabilityPoint(BaseModel):
    class Config:  
        use_enum_values = True
    """data for describing one point of permebility"""
    value: float
    """Permeability value"""
    frequency: Optional[float] = None
    """Frequency of the Magnetic field, in Hz"""
    magneticFieldDcBias: Optional[float] = None
    """DC bias in the magnetic field, in A/m"""
    magneticFluxDensityPeak: Optional[float] = None
    """magnetic flux density peak for the field value, in T"""
    modifiers: Optional[Dict[str, InitialPermeabilitModifier]] = None
    """The initial permeability of a magnetic material according to its manufacturer"""
    temperature: Optional[float] = None
    """temperature for the field value, in Celsius"""
    tolerance: Optional[float] = None
    """tolerance for the field value"""


class Permeabilities(BaseModel):
    class Config:  
        use_enum_values = True
    """The data regarding the relative permeability of a magnetic material"""
    initial: Union[PermeabilityPoint, List[PermeabilityPoint]]
    amplitude: Optional[Union[PermeabilityPoint, List[PermeabilityPoint]]] = None


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
    magneticFluxDensity: OperatingPointExcitation
    origin: str
    """origin of the data"""
    temperature: float
    """temperature value, in Celsius"""
    value: float
    """volumetric losses value, in W/m3"""


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


class CoreLossesMethodType(Enum):
    magnetics = "magnetics"
    micrometals = "micrometals"
    roshen = "roshen"
    steinmetz = "steinmetz"


class SteinmetzCoreLossesMethodRangeDatum(BaseModel):
    class Config:  
        use_enum_values = True
    alpha: float
    """frequency power coefficient alpha"""
    beta: float
    """magnetic flux density power coefficient beta"""
    k: float
    """Proportional coefficient k"""
    ct0: Optional[float] = None
    """Constant temperature coefficient ct0"""
    ct1: Optional[float] = None
    """Proportional negative temperature coefficient ct1"""
    ct2: Optional[float] = None
    """Square temperature coefficient ct2"""
    maximumFrequency: Optional[float] = None
    """maximum frequency for which the coefficients are valid, in Hz"""
    minimumFrequency: Optional[float] = None
    """minimum frequency for which the coefficients are valid, in Hz"""


class CoreLossesMethodData(BaseModel):
    class Config:  
        use_enum_values = True
    """Steinmetz coefficients for estimating volumetric losses in a given frequency range
    
    Roshen coefficients for estimating volumetric losses
    
    Micrometals method for estimating volumetric losses
    
    Magnetics method for estimating volumetric losses
    """
    method: CoreLossesMethodType
    """Name of this method"""
    ranges: Optional[List[SteinmetzCoreLossesMethodRangeDatum]] = None
    coefficients: Optional[RoshenAdditionalCoefficients] = None
    """List of coefficients for taking into account the excess losses and the dependencies of
    the resistivity
    """
    referenceVolumetricLosses: Optional[List[VolumetricLossesPoint]] = None
    """List of reference volumetric losses used to estimate excess eddy current losses"""
    a: Optional[float] = None
    b: Optional[float] = None
    c: Optional[float] = None
    d: Optional[float] = None


class CoreMaterial(BaseModel):
    class Config:  
        use_enum_values = True
    """A material for the magnetic cores"""

    manufacturerInfo: ManufacturerInfo
    material: MaterialEnum
    """The composition of a magnetic material"""

    name: str
    """The name of a magnetic material"""

    permeability: Permeabilities
    """The data regarding the relative permeability of a magnetic material"""

    resistivity: List[ResistivityPoint]
    """Resistivity value according to manufacturer"""

    saturation: List[SaturationElement]
    """BH Cycle points where a non-negligible increase in magnetic field produces a negligible
    increase of magnetic flux density
    """
    type: CoreMaterialType
    """The type of a magnetic material"""

    volumetricLosses: Dict[str, List[Union[CoreLossesMethodData, List[VolumetricLossesPoint]]]]
    """The data regarding the volumetric losses of a magnetic material"""

    bhCycle: Optional[List[SaturationElement]] = None
    coerciveForce: Optional[List[SaturationElement]] = None
    """BH Cycle points where the magnetic flux density is 0"""

    curieTemperature: Optional[float] = None
    """The temperature at which this material losses all ferromagnetism"""

    density: Optional[float] = None
    """Density value according to manufacturer, in kg/m3"""

    family: Optional[str] = None
    """The family of a magnetic material according to its manufacturer"""

    heatCapacity: Optional[DimensionWithTolerance] = None
    """Heat capacity value according to manufacturer, in J/Kg/K"""

    heatConductivity: Optional[DimensionWithTolerance] = None
    """Heat conductivity value according to manufacturer, in W/m/K"""

    materialComposition: Optional[MaterialCompositionEnum] = None
    """The composition of a magnetic material"""

    remanence: Optional[List[SaturationElement]] = None
    """BH Cycle points where the magnetic field is 0"""


class CoreShapeFamily(Enum):
    """The family of a magnetic shape"""
    c = "c"
    drum = "drum"
    e = "e"
    ec = "ec"
    efd = "efd"
    ei = "ei"
    el = "el"
    elp = "elp"
    ep = "ep"
    epx = "epx"
    eq = "eq"
    er = "er"
    etd = "etd"
    h = "h"
    lp = "lp"
    p = "p"
    planare = "planar e"
    planarel = "planar el"
    planarer = "planar er"
    pm = "pm"
    pq = "pq"
    pqi = "pqi"
    rm = "rm"
    rod = "rod"
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


class CoreShape(BaseModel):
    class Config:  
        use_enum_values = True
    """A shape for the magnetic cores"""
    family: CoreShapeFamily
    """The family of a magnetic shape"""
    type: FunctionalDescriptionType
    """The type of a magnetic shape"""
    aliases: Optional[List[str]] = None
    """Alternative names of a magnetic shape"""
    dimensions: Optional[Dict[str, Union[DimensionWithTolerance, float]]] = None
    """The dimensions of a magnetic shape, keys must be as defined in EN 62317"""
    familySubtype: Optional[str] = None
    """The subtype of the shape, in case there are more than one"""
    magneticCircuit: Optional[MagneticCircuit] = None
    """Describes if the magnetic circuit of the shape is open, and can be combined with others;
    or closed, and has to be used by itself
    """
    name: Optional[str] = None
    """The name of a magnetic shape"""


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
    gapping: List[CoreGap]
    """The lists of gaps in the magnetic core"""
    material: Union[CoreMaterial, str]
    shape: Union[CoreShape, str]
    type: CoreType
    """The type of core"""
    coating: Optional[Coating] = None
    """The coating of the core"""
    numberStacks: Optional[int] = None
    """The number of stacked cores"""


class Machining(BaseModel):
    class Config:  
        use_enum_values = True
    """Data describing the machining applied to a piece"""
    coordinates: List[float]
    """The coordinates of the start of the machining, referred to the top of the main column of
    the piece
    """
    length: float
    """Length of the machining"""


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
    coordinates: List[float]
    """The coordinates of the top of the piece, referred to the center of the main column
    
    The coordinates of the center of the gap, referred to the center of the main column
    """
    type: CoreGeometricalDescriptionElementType
    """The type of piece
    
    The type of spacer
    """
    machining: Optional[List[Machining]] = None
    material: Optional[Union[CoreMaterial, str]] = None
    rotation: Optional[List[float]] = None
    """The rotation of the top of the piece from its original state, referred to the center of
    the main column
    """
    shape: Optional[Union[CoreShape, str]] = None
    dimensions: Optional[List[float]] = None
    """Dimensions of the cube defining the spacer"""
    insulationMaterial: Optional[Union[InsulationMaterial, str]] = None
    """Material of the spacer"""


class ColumnType(Enum):
    """Name of the column"""
    central = "central"
    lateral = "lateral"


class ColumnElement(BaseModel):
    class Config:  
        use_enum_values = True
    """Data describing a column of the core"""
    area: float
    """Area of the section column, normal to the magnetic flux direction"""
    coordinates: List[float]
    """The coordinates of the center of the column, referred to the center of the main column.
    In the case of half-sets, the center will be in the top point, where it would join
    another half-set
    """
    depth: float
    """Depth of the column"""
    height: float
    """Height of the column"""
    shape: ColumnShape
    type: ColumnType
    """Name of the column"""
    width: float
    """Width of the column"""
    minimumDepth: Optional[float] = None
    """Minimum depth of the column, if irregular"""
    minimumWidth: Optional[float] = None
    """Minimum width of the column, if irregular"""


class EffectiveParameters(BaseModel):
    class Config:  
        use_enum_values = True
    """Effective data of the magnetic core"""
    effectiveArea: float
    """This is the equivalent section that the magnetic flux traverses, because the shape of the
    core is not uniform and its section changes along the path
    """
    effectiveLength: float
    """This is the equivalent length that the magnetic flux travels through the core."""
    effectiveVolume: float
    """This is the product of the effective length by the effective area, and represents the
    equivalent volume that is magnetized by the field
    """
    minimumArea: float
    """This is the minimum area seen by the magnetic flux along its path"""


class CoreProcessedDescription(BaseModel):
    class Config:  
        use_enum_values = True
    """The data from the core after been processed, and ready to use by the analytical models"""
    columns: List[ColumnElement]
    """List of columns in the core"""
    depth: float
    """Total depth of the core"""
    effectiveParameters: EffectiveParameters
    height: float
    """Total height of the core"""
    width: float
    """Total width of the core"""
    windingWindows: List[WindingWindowElement]
    """List of winding windows, all elements in the list must be of the same type"""


class MagneticCore(BaseModel):
    class Config:  
        use_enum_values = True
    """Data describing the magnetic core.
    
    The description of a magnetic core
    """
    functionalDescription: CoreFunctionalDescription
    """The data from the core based on its function, in a way that can be used by analytical
    models.
    """
    distributorsInfo: Optional[List[DistributorInfo]] = None
    """The lists of distributors of the magnetic core"""
    geometricalDescription: Optional[List[CoreGeometricalDescriptionElement]] = None
    """List with data from the core based on its geometrical description, in a way that can be
    used by CAD models.
    """
    manufacturerInfo: Optional[ManufacturerInfo] = None
    name: Optional[str] = None
    """The name of core"""
    processedDescription: Optional[CoreProcessedDescription] = None
    """The data from the core after been processed, and ready to use by the analytical models"""


class MagneticManufacturerRecommendations(BaseModel):
    class Config:  
        use_enum_values = True
    ratedCurrent: Optional[float] = None
    """The manufacturer's rated current for this part"""
    ratedCurrentTemperatureRise: Optional[float] = None
    """The temperature rise for which the rated current is calculated"""
    ratedMagneticFlux: Optional[float] = None
    """The manufacturer's rated magnetic flux or volt-seconds for this part"""
    saturationCurrent: Optional[float] = None
    """The manufacturer's saturation current for this part"""
    saturationCurrentInductanceDrop: Optional[float] = None
    """Percentage of inductance drop at saturation current"""


class MagneticManufacturerInfo(BaseModel):
    class Config:  
        use_enum_values = True
    name: str
    """The name of the manufacturer of the part"""
    cost: Optional[str] = None
    """The manufacturer's price for this part"""
    datasheetUrl: Optional[str] = None
    """The manufacturer's URL to the datasheet of the product"""
    family: Optional[str] = None
    """The family of a magnetic, as defined by the manufacturer"""
    recommendations: Optional[MagneticManufacturerRecommendations] = None
    reference: Optional[str] = None
    """The manufacturer's reference of this part"""
    status: Optional[Status] = None
    """The production status of a part according to its manufacturer"""


class Magnetic(BaseModel):
    class Config:  
        use_enum_values = True
    """The description of a magnetic"""
    coil: Coil
    """Data describing the coil"""
    core: MagneticCore
    """Data describing the magnetic core."""
    distributorsInfo: Optional[List[DistributorInfo]] = None
    """The lists of distributors of the magnetic"""
    manufacturerInfo: Optional[MagneticManufacturerInfo] = None
    rotation: Optional[List[float]] = None
    """The rotation of the magnetic, by default the winding column goes vertical"""


class ResultOrigin(Enum):
    """Origin of the value of the result"""
    manufacturer = "manufacturer"
    measurement = "measurement"
    simulation = "simulation"


class CoreLossesOutput(BaseModel):
    class Config:  
        use_enum_values = True
    """Data describing the output core losses
    
    Data describing the core losses and the intermediate inputs used to calculate them
    """
    coreLosses: float
    """Value of the core losses"""
    methodUsed: str
    """Model used to calculate the core losses in the case of simulation, or method used to
    measure it
    """
    origin: ResultOrigin
    eddyCurrentCoreLosses: Optional[float] = None
    """Part of the core losses due to eddy currents"""
    hysteresisCoreLosses: Optional[float] = None
    """Part of the core losses due to hysteresis"""
    magneticFluxDensity: Optional[SignalDescriptor] = None
    """Excitation of the B field that produced the core losses"""
    temperature: Optional[float] = None
    """temperature in the core that produced the core losses"""
    volumetricLosses: Optional[float] = None
    """Volumetric value of the core losses"""


class VoltageType(Enum):
    """Type of the voltage"""
    AC = "AC"
    DC = "DC"


class DielectricVoltage(BaseModel):
    class Config:  
        use_enum_values = True
    """Data describing the output insulation that the magnetic has
    
    List of voltages that the magnetic can withstand
    """
    origin: ResultOrigin
    """Origin of the value of the result"""
    voltage: float
    """Voltage that the magnetic withstands"""
    voltageType: VoltageType
    """Type of the voltage"""
    duration: Optional[float] = None
    """Duration of the voltate, or undefined if the field is not present"""
    methodUsed: Optional[str] = None
    """Model used to calculate the voltage in the case of simulation, or method used to measure
    it
    """


class InsulationCoordinationOutput(BaseModel):
    class Config:  
        use_enum_values = True
    """Data describing the output insulation coordination that the magnetic has
    
    List of voltages that the magnetic can withstand
    """
    clearance: float
    """Clearance required for this magnetic"""
    creepageDistance: float
    """Creepage distance required for this magnetic"""
    distanceThroughInsulation: float
    """Distance through insulation required for this magnetic"""
    withstandVoltage: float
    """Voltage that the magnetic withstands"""
    withstandVoltageDuration: Optional[float] = None
    """Duration of the voltate, or undefined if the field is not present"""
    withstandVoltageType: Optional[VoltageType] = None
    """Type of the voltage"""


class LeakageInductanceOutput(BaseModel):
    class Config:  
        use_enum_values = True
    """Data describing the output magnetic strength field
    
    Data describing the leakage inductance and the intermediate inputs used to calculate them
    """
    leakageInductancePerWinding: List[DimensionWithTolerance]
    methodUsed: str
    """Model used to calculate the leakage inductance in the case of simulation, or method used
    to measure it
    """
    origin: ResultOrigin


class AirGapReluctanceOutput(BaseModel):
    class Config:  
        use_enum_values = True
    """Data describing the reluctance of an air gap"""
    fringingFactor: float
    """Value of the Fringing Factor"""
    maximumStorableMagneticEnergy: float
    """Value of the maximum magnetic energy storable in the gap"""
    methodUsed: str
    """Model used to calculate the magnetizing inductance in the case of simulation, or method
    used to measure it
    """
    origin: ResultOrigin
    reluctance: float
    """Value of the reluctance of the gap"""


class MagnetizingInductanceOutput(BaseModel):
    class Config:  
        use_enum_values = True
    """Data describing the output magnetic strength field
    
    Data describing the magnetizing inductance and the intermediate inputs used to calculate
    them
    """
    coreReluctance: float
    """Value of the reluctance of the core"""
    magnetizingInductance: DimensionWithTolerance
    """Value of the magnetizing inductance"""
    methodUsed: str
    """Model used to calculate the magnetizing inductance in the case of simulation, or method
    used to measure it
    """
    origin: ResultOrigin
    gappingReluctance: Optional[float] = None
    """Value of the reluctance of the gaps"""
    maximumFringingFactor: Optional[float] = None
    """Maximum value of the fringing of the gaps"""
    maximumMagneticEnergyCore: Optional[float] = None
    """Value of the maximum magnetic energy storable in the core"""
    maximumStorableMagneticEnergyGapping: Optional[float] = None
    """Value of the maximum magnetic energy storable in the gaps"""
    reluctancePerGap: Optional[List[AirGapReluctanceOutput]] = None
    """Value of the maximum magnetic energy storable in the gaps"""
    ungappedCoreReluctance: Optional[float] = None
    """Value of the reluctance of the core"""


class SixCapacitorNetworkPerWinding(BaseModel):
    class Config:  
        use_enum_values = True
    """Network of six equivalent capacitors that describe the capacitance between two given
    windings
    """
    C1: float
    C2: float
    C3: float
    C4: float
    C5: float
    C6: float


class TripoleCapacitancePerWinding(BaseModel):
    class Config:  
        use_enum_values = True
    """The three values of a three input electrostatic multipole that describe the capacitance
    between two given windings
    """
    C1: float
    C2: float
    C3: float


class StrayCapacitanceOutput(BaseModel):
    class Config:  
        use_enum_values = True
    """Data describing the output stray capacitance
    
    Data describing the stray capacitance and the intermediate inputs used to calculate them
    """
    methodUsed: str
    """Model used to calculate the stray capacitance in the case of simulation, or method used
    to measure it
    """
    origin: ResultOrigin
    """Origin of the value of the result"""
    sixCapacitorNetworkPerWinding: Optional[SixCapacitorNetworkPerWinding] = None
    """Network of six equivalent capacitors that describe the capacitance between two given
    windings
    """
    tripoleCapacitancePerWinding: Optional[TripoleCapacitancePerWinding] = None
    """The three values of a three input electrostatic multipole that describe the capacitance
    between two given windings
    """


class TemperaturePoint(BaseModel):
    class Config:  
        use_enum_values = True
    coordinates: List[float]
    """The coordinates of the temperature point, referred to the center of the main column"""
    value: float
    """temperature at the point, in Celsius"""


class TemperatureOutput(BaseModel):
    class Config:  
        use_enum_values = True
    """Data describing the output temperature
    
    Data describing the temperature and the intermediate inputs used to calculate them
    """
    maximumTemperature: float
    """maximum temperature reached"""
    methodUsed: str
    """Model used to calculate the temperature in the case of simulation, or method used to
    measure it
    """
    origin: ResultOrigin
    bulkThermalResistance: Optional[float] = None
    """bulk thermal resistance of the whole magnetic"""
    initialTemperature: Optional[float] = None
    """Temperature of the magnetic before it started working. If missing ambient temperature
    must be assumed
    """
    temperaturePoint: Optional[TemperaturePoint] = None


class ResistanceMatrixAtFrequency(BaseModel):
    class Config:  
        use_enum_values = True
    frequency: Optional[float] = None
    """Frequency of the resitance matrix"""
    matrix: Optional[List[List[DimensionWithTolerance]]] = None


class OhmicLosses(BaseModel):
    class Config:  
        use_enum_values = True
    """List of value of the winding ohmic losses"""
    losses: float
    """Value of the losses"""
    origin: ResultOrigin
    """Origin of the value of the result"""
    methodUsed: Optional[str] = None
    """Model used to calculate the magnetizing inductance in the case of simulation, or method
    used to measure it
    """


class WindingLossElement(BaseModel):
    class Config:  
        use_enum_values = True
    """List of value of the winding proximity losses per harmonic
    
    Data describing the losses due to either DC, skin effect, or proximity effect; in a given
    element, which can be winding, section, layer or physical turn
    
    List of value of the winding skin losses per harmonic
    """
    harmonicFrequencies: List[float]
    """List of frequencies of the harmonics that are producing losses"""
    lossesPerHarmonic: List[float]
    """Losses produced by each harmonic"""
    methodUsed: str
    """Model used to calculate the magnetizing inductance in the case of simulation, or method
    used to measure it
    """
    origin: ResultOrigin


class WindingLossesPerElement(BaseModel):
    class Config:  
        use_enum_values = True
    ohmicLosses: Optional[OhmicLosses] = None
    """List of value of the winding ohmic losses"""
    proximityEffectLosses: Optional[WindingLossElement] = None
    """List of value of the winding proximity losses per harmonic"""
    skinEffectLosses: Optional[WindingLossElement] = None
    """List of value of the winding skin losses per harmonic"""


class WindingLossesOutput(BaseModel):
    class Config:  
        use_enum_values = True
    """Data describing the output winding losses
    
    Data describing the winding losses and the intermediate inputs used to calculate them
    """
    methodUsed: str
    """Model used to calculate the winding losses in the case of simulation, or method used to
    measure it
    """
    origin: ResultOrigin
    windingLosses: float
    """Value of the winding losses"""
    currentDividerPerTurn: Optional[List[float]] = None
    """Excitation of the current per physical turn that produced the winding losses"""
    currentPerWinding: Optional[OperatingPoint] = None
    """Excitation of the current per winding that produced the winding losses"""
    dcResistancePerTurn: Optional[List[float]] = None
    """List of DC resistance per turn"""
    dcResistancePerWinding: Optional[List[float]] = None
    """List of DC resistance per winding"""
    resistanceMatrix: Optional[List[ResistanceMatrixAtFrequency]] = None
    """List of resistance matrix per frequency"""
    temperature: Optional[float] = None
    """temperature in the winding that produced the winding losses"""
    windingLossesPerLayer: Optional[List[WindingLossesPerElement]] = None
    windingLossesPerSection: Optional[List[WindingLossesPerElement]] = None
    windingLossesPerTurn: Optional[List[WindingLossesPerElement]] = None
    windingLossesPerWinding: Optional[List[WindingLossesPerElement]] = None


class FieldPoint(BaseModel):
    class Config:  
        use_enum_values = True
    """Data describing the value of a field in a 2D or 3D space"""
    point: List[float]
    """The coordinates of the point of the field"""
    value: float
    """Value of the field at this point"""
    label: Optional[str] = None
    """If this point has some special significance, can be identified with this label"""
    rotation: Optional[float] = None
    """Rotation of the rectangle defining the turn, in degrees"""
    turnIndex: Optional[int] = None
    """If this field point is inside of a wire, this is the index of the turn"""
    turnLength: Optional[float] = None
    """If this field point is inside of a wire, this is the length of the turn"""


class Field(BaseModel):
    class Config:  
        use_enum_values = True
    """Data describing a field in a 2D or 3D space"""
    data: List[FieldPoint]
    """Value of the magnetizing inductance"""
    frequency: float
    """Value of the field at this point"""


class WindingWindowCurrentFieldOutput(BaseModel):
    class Config:  
        use_enum_values = True
    """Data describing the output current field
    
    Data describing the curren in the different chunks used in field calculation
    """
    fieldPerFrequency: List[Field]
    methodUsed: str
    """Model used to calculate the current field"""
    origin: ResultOrigin


class ComplexFieldPoint(BaseModel):
    class Config:  
        use_enum_values = True
    """Data describing the complex value of a field in a 2D or 3D space"""
    imaginary: float
    """Imaginary value of the field at this point"""
    point: List[float]
    """The coordinates of the point of the field"""
    real: float
    """Real value of the field at this point"""
    label: Optional[str] = None
    """If this point has some special significance, can be identified with this label"""
    turnIndex: Optional[int] = None
    """If this field point is inside of a wire, this is the index of the turn"""
    turnLength: Optional[float] = None
    """If this field point is inside of a wire, this is the length of the turn"""


class ComplexField(BaseModel):
    class Config:  
        use_enum_values = True
    """Data describing a field in a 2D or 3D space"""
    data: List[ComplexFieldPoint]
    """Value of the magnetizing inductance"""
    frequency: float
    """Value of the field at this point"""


class WindingWindowMagneticStrengthFieldOutput(BaseModel):
    class Config:  
        use_enum_values = True
    """Data describing the output magnetic strength field"""
    fieldPerFrequency: List[ComplexField]
    methodUsed: str
    """Model used to calculate the magnetic strength field"""
    origin: ResultOrigin


class Outputs(BaseModel):
    class Config:  
        use_enum_values = True
    """The description of the outputs that result of simulating a Magnetic"""
    coreLosses: Optional[CoreLossesOutput] = None
    """Data describing the output core losses"""
    insulation: Optional[List[DielectricVoltage]] = None
    """Data describing the output insulation that the magnetic has"""
    insulationCoordination: Optional[InsulationCoordinationOutput] = None
    """Data describing the output insulation coordination that the magnetic has"""
    leakageInductance: Optional[LeakageInductanceOutput] = None
    """Data describing the output magnetic strength field"""
    magnetizingInductance: Optional[MagnetizingInductanceOutput] = None
    """Data describing the output magnetic strength field"""
    strayCapacitance: Optional[List[StrayCapacitanceOutput]] = None
    """Data describing the output stray capacitance"""
    temperature: Optional[TemperatureOutput] = None
    """Data describing the output temperature"""
    windingLosses: Optional[WindingLossesOutput] = None
    """Data describing the output winding losses"""
    windingWindowCurrentDensityField: Optional[WindingWindowCurrentFieldOutput] = None
    """Data describing the output current field"""
    windingWindowCurrentField: Optional[WindingWindowCurrentFieldOutput] = None
    """Data describing the output current field"""
    windingWindowMagneticStrengthField: Optional[WindingWindowMagneticStrengthFieldOutput] = None
    """Data describing the output magnetic strength field"""


class Mas(BaseModel):
    class Config:  
        use_enum_values = True
    """All the data structure used in the Magnetic Agnostic Structure"""
    inputs: Inputs
    """The description of the inputs that can be used to design a Magnetic"""
    magnetic: Magnetic
    """The description of a magnetic"""
    outputs: List[Outputs]
    """The description of the outputs that are produced after designing a Magnetic"""
