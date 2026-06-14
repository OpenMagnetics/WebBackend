import copy
import sys
import os
import hashlib
import time
import ast
import base64
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from mas_models import MagneticCore, CoreShape
from celery import Celery
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../MVB/src/OpenMagneticsVirtualBuilder')))
from OpenMagneticsVirtualBuilder.builder import Builder as ShapeBuilder  # noqa: E402
from models import PlotCacheTable

app = Celery('plots', backend='rpc://', broker='pyamqp://guest@localhost//')


def purge_queue():
    print("Purging queue")
    app.control.purge()


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
    cache = PlotCacheTable()

    cached_datum = cache.read_plot(hash_value)
    if cached_datum is not None:
        print("Hit in cache!")
        return cached_datum

    step_path, stl_path = ShapeBuilder("FreeCAD").get_core(project_name=hash_value,
                                                           geometrical_description=core['geometricalDescription'],
                                                           output_path=f"{temp_folder}/cores")
    path = stl_path if stl_or_not_step else step_path

    print(path)
    if path is None:
        return None

    with open(path, "rb") as stl:
        data = stl.read()
        data = base64.b64encode(data).decode('utf-8')
        cache.insert_plot(hash_value, data)
        return data


@app.task
def task_generate_core_technical_drawing(data, temp_folder):
    if 'familySubtype' in data:
        data['familySubtype'] = str(data['familySubtype'])

    coreShape = CoreShape(**data)
    coreShape = coreShape.dict()
    aux = {
        "coreShape": coreShape,
    }
    hash_value = hashlib.sha256(str(aux).encode()).hexdigest()
    cache = PlotCacheTable()

    cached_datum = cache.read_plot(hash_value)
    if cached_datum is not None:
        print("Hit in cache!")
        return ast.literal_eval(cached_datum)

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
        cache.insert_plot(hash_value, str(views))
        return views


@app.task
def task_generate_gapping_technical_drawing(data, temp_folder):
    if 'familySubtype' in data['functionalDescription']['shape']:
        data['functionalDescription']['shape']['familySubtype'] = str(data['functionalDescription']['shape']['familySubtype'])

    core = MagneticCore(**data)
    core = core.dict()
    aux = {
        "core": core,
    }
    hash_value = hashlib.sha256(str(aux).encode()).hexdigest()
    cache = PlotCacheTable()

    cached_datum = cache.read_plot(hash_value)
    if cached_datum is not None:
        print("Hit in cache!")
        return ast.literal_eval(cached_datum)

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
        cache.insert_plot(hash_value, str(views))
        return views
