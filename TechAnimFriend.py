bl_info = {
    "name": "TechAnim Friend",
    "author": "Aleksandr Dymov",
    "version": (1, 8),
    "blender": (4, 2, 2),
    "location": "3D View > Sidebar > Item",
    "description": "Tools to assist technical animators",
    "category": "Rigging",
}

import bpy
import bmesh
from bpy.props import IntProperty, FloatProperty

# Operator CleanUpWeightsOperator
class CleanUpWeightsOperator(bpy.types.Operator):
    """Clean up weights: remove weights below threshold and limit max influences per vertex"""
    bl_idname = "object.clean_up_weights"
    bl_label = "Clean Up Weights"
    bl_options = {'REGISTER', 'UNDO'}

    threshold: FloatProperty(
        name="Threshold",
        description="Weights below this value will be removed",
        default=0.050,
        min=0.0,
        max=1.0,
    )

    max_influences: IntProperty(
        name="Max Influences",
        description="Maximum number of bone influences per vertex",
        default=4,
        min=1,
    )

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'MESH'

    def execute(self, context):
        obj = context.active_object

        # Switch to Object Mode to access vertex groups
        current_mode = context.mode
        if current_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        mesh = obj.data
        vgroups = obj.vertex_groups

        if not vgroups:
            self.report({'WARNING'}, "Object has no vertex groups")
            bpy.ops.object.mode_set(mode=current_mode)
            return {'CANCELLED'}

        num_weights_removed = 0
        num_vertices_adjusted = 0

        for vert in mesh.vertices:
            # Get all groups and weights for this vertex
            weights = []
            for g in vert.groups:
                group = vgroups[g.group]
                weight = g.weight
                if weight < self.threshold:
                    # Remove weight below threshold
                    group.remove([vert.index])
                    num_weights_removed += 1
                else:
                    weights.append((group, weight))

            # Sort weights in descending order
            weights.sort(key=lambda x: x[1], reverse=True)

            if len(weights) > self.max_influences:
                # Remove smallest weights to limit max influences
                for group, weight in weights[self.max_influences:]:
                    group.remove([vert.index])
                    num_weights_removed += 1
                num_vertices_adjusted += 1

        # Restore original mode
        if current_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode=current_mode)

        self.report({'INFO'}, f"Removed {num_weights_removed} weights; adjusted {num_vertices_adjusted} vertices to have max {self.max_influences} influences")
        return {'FINISHED'}

# Other existing operators...

# Operator SmoothSelectedVerticesWeightsOperator
class SmoothSelectedVerticesWeightsOperator(bpy.types.Operator):
    """Smooth weights of selected vertices over specified iterations"""
    bl_idname = "object.smooth_selected_vertices_weights"
    bl_label = "Smooth Selected Vertices Weights"
    bl_options = {'REGISTER', 'UNDO'}

    iterations: IntProperty(
        name="Iterations",
        description="Number of smoothing iterations",
        default=10,
        min=1,
        max=100,
    )

    threshold: FloatProperty(
        name="Threshold",
        description="Weights below this value will be removed",
        default=0.050,
        min=0.0,
        max=1.0,
    )

    @classmethod
    def poll(cls, context):
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

        # Get vertex groups
        vgroups = obj.vertex_groups

        if not vgroups:
            self.report({'WARNING'}, "Object has no vertex groups")
            bpy.ops.object.mode_set(mode='EDIT')
            return {'CANCELLED'}

        all_vertices = obj.data.vertices

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
                    v = all_vertices[idx]

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

                # Apply new weights with threshold-based removal
                for idx, weight in new_weights.items():
                    if weight < self.threshold:
                        vgroup.remove([idx])
                    else:
                        vgroup.add([idx], weight, 'REPLACE')

        # Switch back to Edit Mode
        bpy.ops.object.mode_set(mode='EDIT')

        # Update the mesh
        bmesh.update_edit_mesh(mesh)

        self.report({'INFO'}, f"Weights smoothed over {self.iterations} iterations with weights below {self.threshold:.3f} removed")
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

# Panel class TechAnimToolsItemPanel
class TechAnimToolsItemPanel(bpy.types.Panel):
    """Panel for Tech Animator's Assistant in Item tab"""
    bl_label = "Tech Anim Tools"
    bl_idname = "VIEW3D_PT_techanim_tools_item"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = "mesh_edit"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)

        # Кнопки доступны только при активном объекте типа Mesh
        if context.active_object and context.active_object.type == 'MESH':
            col.operator("object.clean_up_weights", text="Clean Up Weights", icon='BRUSH_DATA')
            col.operator("object.smooth_selected_vertices_weights", text="Smooth Selected Vertices Weights", icon='MOD_SMOOTH')
            col.operator("object.check_weight_amount", text="Check Weight Amount", icon='MOD_VERTEX_WEIGHT')

# Other existing panels and operators...

# Register classes
classes = (
    CleanUpWeightsOperator,
    SmoothSelectedVerticesWeightsOperator,
    CheckWeightAmountOperator,
    TechAnimToolsItemPanel,
    # Other classes...
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
