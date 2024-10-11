bl_info = {
    "name": "TechAnim Friend",
    "author": "Aleksandr Dymov",
    "version": (1, 3),
    "blender": (4, 2, 2),
    "location": "3D View > Sidebar > Tech Anim Tools",
    "description": "Tools to assist technical animators",
    "category": "Rigging",
}

import bpy
import bmesh
from bpy.props import IntProperty
from bpy.app.translations import pgettext_iface as iface_

# Operator CopyBonesTransformsOperator
class CopyBonesTransformsOperator(bpy.types.Operator):
    """Copy bone transforms from donor to recipient armature"""
    bl_idname = "object.copy_bones_transforms"
    bl_label = "Copy Bones Transforms"
    bl_options = {'REGISTER', 'UNDO'}

    bl_description = iface_("Copy bone transforms from the donor armature to selected recipient armatures.")

    def execute(self, context):
        # Your operator code
        return {'FINISHED'}

# Operator CreateConstraintsOperator
class CreateConstraintsOperator(bpy.types.Operator):
    """Create constraints from donor to recipient armature"""
    bl_idname = "object.create_constraints"
    bl_label = "Create Constraints"
    bl_options = {'REGISTER', 'UNDO'}

    bl_description = iface_("Create Copy Transforms constraints from the donor armature to selected recipient armatures.")

    def execute(self, context):
        # Your operator code
        return {'FINISHED'}

# Operator RemoveConstraintsOperator
class RemoveConstraintsOperator(bpy.types.Operator):
    """Remove constraints from recipient armature"""
    bl_idname = "object.remove_constraints"
    bl_label = "Remove Constraints"
    bl_options = {'REGISTER', 'UNDO'}

    bl_description = iface_("Remove Copy Transforms constraints from selected recipient armatures.")

    def execute(self, context):
        # Your operator code
        return {'FINISHED'}

# Operator CheckWeightAmountOperator
class CheckWeightAmountOperator(bpy.types.Operator):
    """Select vertices influenced by more than a specified number of bones"""
    bl_idname = "object.check_weight_amount"
    bl_label = "Check Weight Amount"
    bl_options = {'REGISTER', 'UNDO'}

    bl_description = iface_("Select vertices that are influenced by more than a specified number of bones.")

    max_influences: IntProperty(
        name=iface_("Max Influences"),
        description=iface_("Maximum number of bone influences per vertex"),
        default=3,
        min=1,
    )

    def execute(self, context):
        # Your operator code
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

# Operator SmoothSelectedVerticesWeightsOperator
class SmoothSelectedVerticesWeightsOperator(bpy.types.Operator):
    """Smooth weights of selected vertices over specified iterations"""
    bl_idname = "object.smooth_selected_vertices_weights"
    bl_label = "Smooth Selected Vertices Weights"
    bl_options = {'REGISTER', 'UNDO'}

    bl_description = iface_("Smooth the weights of selected vertices by averaging with neighboring vertices.")

    iterations: IntProperty(
        name=iface_("Iterations"),
        description=iface_("Number of smoothing iterations"),
        default=10,
        min=1,
        max=100,
    )

    @classmethod
    def poll(cls, context):
        # Operator is available only in Edit Mode and when a Mesh object is active
        return (
            context.active_object is not None and
            context.active_object.type == 'MESH' and
            context.mode == 'EDIT_MESH'
        )

    def execute(self, context):
        obj = context.active_object

        # Ensure we are in Edit Mode
        if context.mode != 'EDIT_MESH':
            self.report({'WARNING'}, "Must be in Edit Mode")
            return {'CANCELLED'}

        mesh = obj.data

        # Create BMesh
        bm = bmesh.from_edit_mesh(mesh)

        # Get indices of selected vertices
        selected_verts_indices = [v.index for v in bm.verts if v.select]

        if not selected_verts_indices:
            self.report({'WARNING'}, "No vertices selected")
            return {'CANCELLED'}

        # Switch to Object Mode to access vertex groups
        bpy.ops.object.mode_set(mode='OBJECT')

        # Get all vertices of the mesh
        all_vertices = obj.data.vertices

        # Get vertex groups
        vgroups = obj.vertex_groups

        if not vgroups:
            self.report({'WARNING'}, "Object has no vertex groups")
            bpy.ops.object.mode_set(mode='EDIT')
            return {'CANCELLED'}

        # Build a dictionary of neighbors for all vertices
        vertex_neighbors = {v.index: set() for v in all_vertices}
        for edge in obj.data.edges:
            v1, v2 = edge.vertices
            vertex_neighbors[v1].add(v2)
            vertex_neighbors[v2].add(v1)

        # Perform smoothing
        for iteration in range(self.iterations):
            # For each vertex group
            for vgroup in vgroups:
                # Store new weights here
                new_weights = {}

                # For each selected vertex
                for idx in selected_verts_indices:
                    v = obj.data.vertices[idx]

                    # Get current weight
                    try:
                        w = vgroup.weight(v.index)
                    except RuntimeError:
                        w = 0.0

                    # Get weights of neighboring vertices
                    neighbor_weights = []
                    for n_idx in vertex_neighbors[v.index]:
                        try:
                            nw = vgroup.weight(n_idx)
                        except RuntimeError:
                            nw = 0.0
                        neighbor_weights.append(nw)

                    # Calculate new weight
                    if neighbor_weights:
                        average_weight = sum(neighbor_weights) / len(neighbor_weights)
                        # Optionally include current vertex weight
                        new_weight = (w + average_weight) / 2
                    else:
                        new_weight = w

                    new_weights[v.index] = new_weight

                # Apply new weights
                for idx, weight in new_weights.items():
                    vgroup.add([idx], weight, 'REPLACE')

        # Switch back to Edit Mode
        bpy.ops.object.mode_set(mode='EDIT')

        # Update the mesh
        bmesh.update_edit_mesh(mesh)

        self.report({'INFO'}, f"Weights smoothed over {self.iterations} iterations")
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

# Panel class TechAnimToolsPanel
class TechAnimToolsPanel(bpy.types.Panel):
    """Panel for Tech Animator's Assistant"""
    bl_label = iface_("Tech Animator's Assistant")
    bl_idname = "VIEW3D_PT_techanim_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = iface_("Tech Anim Tools")

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.label(text=iface_("Bone Operations:"))
        col.operator("object.copy_bones_transforms", text=iface_("Copy Bones Transforms"), icon='BONE_DATA')
        col.operator("object.create_constraints", text=iface_("Create Constraints"), icon='CONSTRAINT_BONE')
        col.operator("object.remove_constraints", text=iface_("Remove Constraints"), icon='X')
        col.separator()
        col.label(text=iface_("Mesh Operations:"))
        col.operator("object.check_weight_amount", text=iface_("Check Weight Amount"), icon='MOD_VERTEX_WEIGHT')

        # Button is available only in Edit Mode
        if context.mode == 'EDIT_MESH':
            col.operator("object.smooth_selected_vertices_weights", text=iface_("Smooth Selected Vertices Weights"), icon='SMOOTH')

# Register classes
classes = (
    CopyBonesTransformsOperator,
    CreateConstraintsOperator,
    RemoveConstraintsOperator,
    CheckWeightAmountOperator,
    SmoothSelectedVerticesWeightsOperator,
    TechAnimToolsPanel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
