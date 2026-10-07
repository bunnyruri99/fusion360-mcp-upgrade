"""Z-buffer CAD render so overlapping assembly parts are shown correctly."""
from pathlib import Path
import cadquery as cq
import vtk

OUT=Path(__file__).resolve().parent/'bracket_corrected'
ESP=Path(r'C:\Users\HunterD\Downloads\esp32-c3-supermini-1.snapshot.2\ESP32-C3 supermini v5.step')

def actor(shape,color,shift=(0,0,0)):
    vertices,triangles=shape.tessellate(.12,.16)
    points=vtk.vtkPoints()
    for p in vertices: points.InsertNextPoint(*p.toTuple())
    cells=vtk.vtkCellArray()
    for triangle in triangles:
        cells.InsertNextCell(3)
        for i in triangle: cells.InsertCellPoint(i)
    poly=vtk.vtkPolyData()
    poly.SetPoints(points); poly.SetPolys(cells)
    normal=vtk.vtkPolyDataNormals()
    normal.SetInputData(poly); normal.SetFeatureAngle(40)
    mapper=vtk.vtkPolyDataMapper(); mapper.SetInputConnection(normal.GetOutputPort())
    a=vtk.vtkActor(); a.SetMapper(mapper); a.SetPosition(*shift)
    a.GetProperty().SetColor(*color)
    a.GetProperty().SetAmbient(.25); a.GetProperty().SetDiffuse(.75)
    return a

shapes=cq.importers.importStep(str(OUT/'assembly.step')).solids().vals()
# Assembly order: frame, keeper, 61 ESP solids, TFT PCB, LCD, AA, 12 hardware.
frame,keeper=shapes[:2]
esp=shapes[2:63]
tft,lcd,aa=shapes[63:66]
hardware=shapes[66:]
assert len(esp)==61 and len(hardware)==12
win=vtk.vtkRenderWindow(); win.SetOffScreenRendering(1); win.SetSize(2100,1000)
for i,(title,pos,explode) in enumerate([
    ('DISPLAY SIDE',(100,-135,130),False),
    ('REAR - USB-C / GPIO',(100,-135,-125),False),
    ('EXPLODED - 2 PRINTED PARTS',(100,-135,125),True)]):
    r=vtk.vtkRenderer(); r.SetViewport(i/3,0,(i+1)/3,1)
    r.SetBackground(.95,.96,.975); win.AddRenderer(r)
    r.AddActor(actor(frame,(.15,.49,.60)))
    r.AddActor(actor(keeper,(.92,.54,.19),(0,0,-13) if explode else (0,0,0)))
    for j,s in enumerate(esp):
        color=(.06,.28,.6) if j==0 else (.67,.70,.72) if j==1 else (.12,.14,.16)
        r.AddActor(actor(s,color,(0,0,-6) if explode else (0,0,0)))
    for s,col in [(tft,(.03,.35,.17)),(lcd,(.055,.065,.075)),(aa,(.11,.15,.18))]:
        r.AddActor(actor(s,col,(0,0,11) if explode else (0,0,0)))
    if not explode:
        for s in hardware: r.AddActor(actor(s,(.65,.69,.72)))
    cam=r.GetActiveCamera(); cam.SetPosition(*pos); cam.SetFocalPoint(10.54,36,-6)
    cam.SetViewUp(0,1,0); cam.ParallelProjectionOn(); cam.SetParallelScale(48)
    r.ResetCameraClippingRange()
    label=vtk.vtkTextActor(); label.SetInput(title); label.SetPosition(25,920)
    prop=label.GetTextProperty(); prop.SetFontSize(22); prop.SetColor(.13,.17,.21)
    r.AddActor2D(label)
    caption=vtk.vtkTextActor()
    caption.SetInput('Actual ESP STEP; TFT is a dimensional proxy.\nFrame = blue  |  Removable keeper = orange')
    caption.SetPosition(25,35); cp=caption.GetTextProperty(); cp.SetFontSize(15); cp.SetColor(.2,.25,.3)
    r.AddActor2D(caption)
win.Render()
f=vtk.vtkWindowToImageFilter(); f.SetInput(win); f.Update()
writer=vtk.vtkPNGWriter(); writer.SetFileName(str(OUT/'preview.png'))
writer.SetInputConnection(f.GetOutputPort()); writer.Write()
print('Saved',OUT/'preview.png')
