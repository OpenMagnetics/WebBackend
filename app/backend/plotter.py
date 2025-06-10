import copy
import sys
import os
import hashlib
import PyMKF
import time
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from mas_models import MagneticCore, CoreShape
from celery import Celery
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../MVB/src/OpenMagneticsVirtualBuilder')))
from OpenMagneticsVirtualBuilder.builder import Builder as ShapeBuilder  # noqa: E402

app = Celery('plots', backend='rpc://', broker='pyamqp://guest@localhost//')


def clean_dimensions(core):
    # Make sure no unwanted dimension gets in
    families = ShapeBuilder("FreeCAD").get_families()
    if "familySubtype" in core['functionalDescription']['shape'] and core['functionalDescription']['shape']['familySubtype'] is not None:
        dimensions = families[core['functionalDescription']['shape']['family']][int(core['functionalDescription']['shape']['familySubtype'])]
    else:
        dimensions = families[core['functionalDescription']['shape']['family']][1]
    aux = copy.deepcopy(core['functionalDescription']['shape']['dimensions'])
    for key, value in core['functionalDescription']['shape']['dimensions'].items():
        if key not in dimensions:
            aux.pop(key)
    core['functionalDescription']['shape']['dimensions'] = aux
    return core


@app.task
def task_generate_core_3d_model(core, temp_folder, stl_or_not_step=True):
    if 'familySubtype' in core['functionalDescription']['shape']:
        core['functionalDescription']['shape']['familySubtype'] = str(core['functionalDescription']['shape']['familySubtype'])

    core = MagneticCore(**core)
    core = core.dict()

    core = clean_dimensions(core)
    if not isinstance(core['functionalDescription']['material'], str):
        core['functionalDescription']['material'] = core['functionalDescription']['material']['name']

    # pprint.pprint(core)
    aux = {
        "core": core,
    }
    hash_value = hashlib.sha256(str(aux).encode()).hexdigest()
    # print(hash_value)

    if stl_or_not_step:
        if os.path.exists(f"{temp_folder}/cores/{hash_value}_core.stl"):
            print("Core stl Hit!")
            with open(f"{temp_folder}/cores/{hash_value}_core.stl", "rb") as stl:
                stl_data = stl.read()
                return stl_data
    else:
        if os.path.exists(f"{temp_folder}/cores/{hash_value}_core.stp"):
            print("Core stp Hit!")
            with open(f"{temp_folder}/cores/{hash_value}_core.stp", "rb") as stp:
                stp_data = stp.read()
                return stp_data

    step_path, stl_path = ShapeBuilder("FreeCAD").get_core(project_name=hash_value,
                                                           geometrical_description=core['geometricalDescription'],
                                                           output_path=f"{temp_folder}/cores")
    path = stl_path if stl_or_not_step else step_path

    print(path)
    if path is None:
        return None

    with open(path, "rb") as stl:
        data = stl.read()
        return data


@app.task
def task_plot_core_and_fields(data, temp_folder):
    aux = {
        "magnetic": data["magnetic"],
        "operatingPoint": data["operatingPoint"],
        "includeFringing": data["includeFringing"],
    }
    hash_value = hashlib.sha256(str(aux).encode()).hexdigest()

    if os.path.exists(f"{temp_folder}/{hash_value}.svg"):
        print("Hit!")
        return f"{temp_folder}/{hash_value}.svg"

    settings = PyMKF.get_settings()
    settings["painterSimpleLitz"] = True
    settings["painterAdvancedLitz"] = False
    settings["painterCciCoordinatesPath"] = "/opt/openmagnetics/cci_coords/coordinates/"
    settings["painterIncludeFringing"] = data["includeFringing"]
    settings["painterColorBobbin"] = "0x7F539796"
    settings["painterColorText"] = "0xd4d4d4"
    settings["painterColorLines"] = "0x1a1a1a"
    settings["painterColorMargin"] = "0x7Ffff05b"
    PyMKF.set_settings(settings)
    result = PyMKF.plot_field(data["magnetic"], data["operatingPoint"], f"{temp_folder}/{hash_value}.svg")
    print("result")
    print(result)
    timeout = 0
    current_size = 0
    while not os.path.exists(f"{temp_folder}/{hash_value}.svg"):
        time.sleep(0.01)
        timeout += 1
        if timeout == 200:
            return None

    timeout = 0
    while os.stat(f"{temp_folder}/{hash_value}.svg").st_size == 0 or current_size != os.stat(f"{temp_folder}/{hash_value}.svg").st_size:
        current_size = os.stat(f"{temp_folder}/{hash_value}.svg").st_size
        time.sleep(0.01)
        timeout += 1
        print(timeout)
        if timeout == 1000:
            return None
    return f"{temp_folder}/{hash_value}.svg"


@app.task
def task_plot_core(data, temp_folder):
    aux = {
        "magnetic": data["magnetic"]
    }
    hash_value = hashlib.sha256(str(aux).encode()).hexdigest()

    if os.path.exists(f"{temp_folder}/{hash_value}.svg"):
        print("Plot core Hit!")
        print(hash_value)
        return f"{temp_folder}/{hash_value}.svg"

    settings = PyMKF.get_settings()
    settings["painterSimpleLitz"] = True
    settings["painterAdvancedLitz"] = False
    settings["painterCciCoordinatesPath"] = "/opt/openmagnetics/cci_coords/coordinates/"
    PyMKF.set_settings(settings)
    PyMKF.plot_turns(data["magnetic"], f"{temp_folder}/{hash_value}.svg")

    timeout = 0
    current_size = 0
    while not os.path.exists(f"{temp_folder}/{hash_value}.svg"):
        time.sleep(0.01)
        timeout += 1
        if timeout == 200:
            return None

    timeout = 0
    while os.stat(f"{temp_folder}/{hash_value}.svg").st_size == 0 or current_size != os.stat(f"{temp_folder}/{hash_value}.svg").st_size:
        current_size = os.stat(f"{temp_folder}/{hash_value}.svg").st_size
        time.sleep(0.01)
        timeout += 1
        if timeout == 1000:
            return None
    return f"{temp_folder}/{hash_value}.svg"


@app.task
def task_plot_wire(data, temp_folder):
    aux = {
        "wire": data["wire"]
    }

    hash_value = hashlib.sha256(str(aux).encode()).hexdigest()

    if os.path.exists(f"{temp_folder}/{hash_value}.svg"):
        print("Hit!")
        return f"{temp_folder}/{hash_value}.svg"

    settings = PyMKF.get_settings()
    settings["painterSimpleLitz"] = False
    settings["painterAdvancedLitz"] = False
    settings["painterColorBobbin"] = "0x539796"
    settings["painterColorMargin"] = "0xfff05b"
    settings["painterCciCoordinatesPath"] = "/opt/openmagnetics/cci_coords/coordinates/"
    PyMKF.set_settings(settings)

    # print(data["wire"])
    PyMKF.plot_wire(data["wire"], f"{temp_folder}/{hash_value}.svg", "/opt/openmagnetics/cci_coords/coordinates/")
    timeout = 0
    current_size = 0
    while not os.path.exists(f"{temp_folder}/{hash_value}.svg"):
        time.sleep(0.01)
        timeout += 1
        if timeout == 200:
            return None

    timeout = 0
    while os.stat(f"{temp_folder}/{hash_value}.svg").st_size == 0 or current_size != os.stat(f"{temp_folder}/{hash_value}.svg").st_size:
        current_size = os.stat(f"{temp_folder}/{hash_value}.svg").st_size
        time.sleep(0.01)
        timeout += 1
        if timeout == 1000:
            return None
    return f"{temp_folder}/{hash_value}.svg"


@app.task
def task_plot_wire_and_current_density(data, temp_folder):
    aux = {
        "wire": data["wire"],
        "operatingPoint": data["operatingPoint"],
    }

    hash_value = hashlib.sha256(str(aux).encode()).hexdigest()

    if os.path.exists(f"{temp_folder}/{hash_value}.svg"):
        print("Hit!")
        return f"{temp_folder}/{hash_value}.svg"

    settings = PyMKF.get_settings()
    settings["painterSimpleLitz"] = False
    settings["painterAdvancedLitz"] = False
    settings["painterCciCoordinatesPath"] = "/opt/openmagnetics/cci_coords/coordinates/"
    PyMKF.set_settings(settings)

    PyMKF.plot_current_density(data["wire"], data["operatingPoint"], f"{temp_folder}/{hash_value}.svg")
    timeout = 0
    current_size = 0
    while not os.path.exists(f"{temp_folder}/{hash_value}.svg"):
        time.sleep(0.01)
        timeout += 1
        if timeout == 200:
            return None

    timeout = 0
    while os.stat(f"{temp_folder}/{hash_value}.svg").st_size == 0 or current_size != os.stat(f"{temp_folder}/{hash_value}.svg").st_size:
        current_size = os.stat(f"{temp_folder}/{hash_value}.svg").st_size
        time.sleep(0.01)
        timeout += 1
        if timeout == 1000:
            return None
    return f"{temp_folder}/{hash_value}.svg"


@app.task
def task_generate_core_technical_drawing(data, temp_folder):
    if 'familySubtype' in data:
        data['familySubtype'] = str(data['familySubtype'])

    coreShape = CoreShape(**data)

    coreShape = coreShape.dict()
    core_builder = ShapeBuilder("FreeCAD").factory(coreShape)
    core_builder.set_output_path(f"{temp_folder}/")
    colors = {
        "projection_color": "#d4d4d4",
        "dimension_color": "#d4d4d4"
    }
    views = core_builder.get_piece_technical_drawing(coreShape, colors)

    if views['top_view'] is None or views['front_view'] is None:
        return None
    else:
        return views


@app.task
def task_generate_gapping_technical_drawing(data, temp_folder):
    if 'familySubtype' in data['functionalDescription']['shape']:
        data['functionalDescription']['shape']['familySubtype'] = str(data['functionalDescription']['shape']['familySubtype'])

    core = MagneticCore(**data)
    core = core.dict()

    colors = {
        "projection_color": "#d4d4d4",
        "dimension_color": "#d4d4d4"
    }

    views = ShapeBuilder("FreeCAD").get_core_gapping_technical_drawing(project_name=core['functionalDescription']['shape']['name'],
                                                                       core_data=core,
                                                                       colors=colors,
                                                                       save_files=False)

    if views['top_view'] is None or views['front_view'] is None:
        return None
    else:
        return views
