#Author-BROOSE
#Description-Places circles at verticie of an inset triangle

import adsk.core, adsk.fusion, adsk.cam, traceback

from typing import Tuple

from math import sqrt

# everything here is in centimeters... for reasons
DISTANCE_FROM_SIDES = 0.25 * 2.54
DIAMETER_CIRCLE = 0.125 * 2.54
TARGET_COMPONENT = 'block 2'
NEW_SKETCH_NAME = 'BROOSE SLAPS'

SKETCH_SIDES = False
SKETCH_CIRCLES = True

def get_moved_point(point : adsk.core.Vector3D, centroid : adsk.core.Vector3D, scale : float) -> adsk.core.Point3D:
    p = point.copy()
    p.subtract(centroid)
    p.scaleBy(scale)
    p.add(centroid)
    return p.asPoint()

def run(context):
    _ui = None
    try:
        _app = adsk.core.Application.get()
        _ui  = _app.userInterface
        _design = adsk.fusion.Design.cast(_app.activeProduct)
        if not _design:
            _ui.messageBox('No active Fusion 360 design', 'No Design')
            return
        
        # get component
        _components = _design.allComponents
        _comp = None
        for _c in range(_components.count):
            _c_impl = _components.item(_c)
            if _c_impl.name == TARGET_COMPONENT:
                _comp = _c_impl
                break
        if not _comp:
            _ui.messageBox('Dadnt find component {} D:'.format(TARGET_COMPONENT))
            return
            
        # get sketch
        _sketch_count = _comp.sketches.count
        if _sketch_count != 1:
            _ui.messageBox('There is either 0 or more than 1 sketch D: (there is actually {})'.format(_sketch_count))
            return
        _original_sketch = _comp.sketches.item(0)
        _original_triangles = _original_sketch.profiles
        
        # new sketch
        xyPlane = _comp.xYConstructionPlane
        _new_sketch : adsk.fusion.Sketch = _comp.sketches.add(xyPlane)
        _new_sketch.name = NEW_SKETCH_NAME

        for _triangle_index in range(_original_triangles.count):

            try:
                # https://math.stackexchange.com/questions/1397456/how-to-scale-a-triangle-such-that-the-distance-between-original-edges-and-new-ed
                _original_triangle : adsk.fusion.Profile = _original_triangles.item(_triangle_index)
                _area_prop : adsk.fusion.AreaProperties = _original_triangle.areaProperties()
                _area = _area_prop.area
                _semi_perimeter = _area_prop.perimeter / 2.0
                _in_radius = _area / _semi_perimeter
                _scale = (_in_radius - DISTANCE_FROM_SIDES) / _in_radius
            
                _original_edges : adsk.fusion.ProfileCurves = _original_triangle.profileLoops.item(0).profileCurves
            
                _edge_1 : adsk.core.Line3D = _original_edges.item(0).geometry
                _edge_2 : adsk.core.Line3D = _original_edges.item(1).geometry
                _edge_3 : adsk.core.Line3D = _original_edges.item(2).geometry

                _original_point_1 = _edge_1.startPoint.asVector()
                _original_point_2 = _edge_1.endPoint.asVector()
                _original_point_3 = _edge_2.startPoint.asVector()

                if _original_point_3 == _original_point_1 or _original_point_3 == _original_point_2:
                    _original_point_3 = _edge_2.endPoint
                if _original_point_3 == _original_point_1 or _original_point_3 == _original_point_2:
                    _ui.messageBox("shoudln't have gotten here")

                a_d = _original_point_3.copy()
                a_d.subtract(_original_point_2)
                a_d = sqrt(a_d.dotProduct(a_d))

                b_d = _original_point_1.copy()
                b_d.subtract(_original_point_3)
                b_d = sqrt(b_d.dotProduct(b_d))

                c_d = _original_point_2.copy()
                c_d.subtract(_original_point_1)
                c_d = sqrt(c_d.dotProduct(c_d))

                a = _original_point_1.copy()
                a.scaleBy(a_d)

                b = _original_point_2.copy()
                b.scaleBy(b_d)

                c = _original_point_3.copy()
                c.scaleBy(c_d)

                _in_center = a.copy()
                _in_center.add(b)
                _in_center.add(c)
                _in_center.scaleBy(1 / _area_prop.perimeter)


                _a = get_moved_point(_original_point_1, _in_center, _scale)
                _b = get_moved_point(_original_point_2, _in_center, _scale)
                _c = get_moved_point(_original_point_3, _in_center, _scale)

                if SKETCH_SIDES:
                    _new_sketch.sketchCurves.sketchLines.addByTwoPoints(_a, _b)
                    _new_sketch.sketchCurves.sketchLines.addByTwoPoints(_b, _c)
                    _new_sketch.sketchCurves.sketchLines.addByTwoPoints(_c, _a)

                if SKETCH_CIRCLES:
                    _radius = DIAMETER_CIRCLE / 2.0
                    _new_sketch.sketchCurves.sketchCircles.addByCenterRadius(_a, _radius)
                    _new_sketch.sketchCurves.sketchCircles.addByCenterRadius(_b, _radius)
                    _new_sketch.sketchCurves.sketchCircles.addByCenterRadius(_c, _radius)
                
            except:
                if _ui:
                    _ui.messageBox('Failed at triangle {}:\n{}'.format(_triangle_index, traceback.format_exc()))
    
        _ui.messageBox("finished")

    except:
        if _ui:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
