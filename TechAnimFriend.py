bl_info = {
    "name": "TechAnim Friend",
    "author": "Aleksandr Dymov",
    "version": (1, 9),
    "blender": (4, 2, 2),
    "location": "3D View > Sidebar > Tech Anim Tools, Item Tab",
    "description": "Tools to assist technical animators",
    "category": "Rigging",
}

import bpy
import bmesh
from bpy.props import IntProperty, FloatProperty

class RemoveConstraintsOperator(bpy.types.Operator):
    """Remove all constraints from selected skeletons"""
    bl_idname = "object.remove_constraints"
    bl_label = "Remove Constraints"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected_objects = context.selected_objects

        if not selected_objects:
            self.report({'WARNING'}, "No armatures selected.")
            return {'CANCELLED'}

        for obj in selected_objects:
            if obj.type == 'ARMATURE':
                for bone in obj.pose.bones:
                    # Removing all constraints for each bone
                    while bone.constraints:
                        bone.constraints.remove(bone.constraints[0])
            else:
                self.report({'WARNING'}, "Selected object is not an armature.")
                return {'CANCELLED'}

        self.report({'INFO'}, "Constraints removed successfully.")
        return {'FINISHED'}


class CreateConstraintsOperator(bpy.types.Operator):
    """Create constraints between selected skeletons"""
    bl_idname = "object.create_constraints"
    bl_label = "Create Constraints"
    bl_options = {'REGISTER', 'UNDO'}

    target_space: bpy.props.EnumProperty(
        items=[
            ('LOCAL', "Local Space", "Use local space for target bones"),
            ('WORLD', "World Space", "Use world space for target bones")
        ],
        name="Target Space",
        default='LOCAL'
    )

    owner_space: bpy.props.EnumProperty(
        items=[
            ('LOCAL', "Local Space", "Use local space for owner bones"),
            ('WORLD', "World Space", "Use world space for owner bones")
        ],
        name="Owner Space",
        default='LOCAL'
    )

    def execute(self, context):
        selected_objects = context.selected_objects

        if len(selected_objects) < 2:
            self.report({'WARNING'}, "Select at least two armatures.")
            return {'CANCELLED'}

        donor_armature = selected_objects[-1]
        recipients = selected_objects[:-1]

        for recipient in recipients:
            if donor_armature.type == 'ARMATURE' and recipient.type == 'ARMATURE':
                for donor_bone in donor_armature.pose.bones:
                    if donor_bone.name in recipient.pose.bones:
                        recipient_bone = recipient.pose.bones[donor_bone.name]

                        # Checking for existing constraints to avoid duplication
                        existing_constraints = [c for c in recipient_bone.constraints if c.target == donor_armature and c.subtarget == donor_bone.name]
                        if not existing_constraints:
                            constraint = recipient_bone.constraints.new('COPY_TRANSFORMS')
                            constraint.target = donor_armature
                            constraint.subtarget = donor_bone.name
                            constraint.target_space = self.target_space
                            constraint.owner_space = self.owner_space
            else:
                self.report({'WARNING'}, "Both objects must be armatures.")
                return {'CANCELLED'}

        self.report({'INFO'}, "Constraints created successfully.")
        return {'FINISHED'}


class CopyBonesTransformsEditModeOperator(bpy.types.Operator):
    """Copy bone transforms in Edit Mode"""
    bl_idname = "object.copy_bones_transforms_edit_mode"
    bl_label = "Copy Bones Transforms (Edit Mode)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected_objects = context.selected_objects

        if len(selected_objects) < 2:
            self.report({'WARNING'}, "Select at least two armatures.")
            return {'CANCELLED'}

        donor_armature = selected_objects[-1]  # последний выбранный
        recipients = selected_objects[:-1]  # все остальные

        # Переключаемся в Edit Mode для всех объектов
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        donor_armature.select_set(True)
        bpy.context.view_layer.objects.active = donor_armature
        bpy.ops.object.mode_set(mode='EDIT')

        for recipient in recipients:
            if donor_armature.type == 'ARMATURE' and recipient.type == 'ARMATURE':
                bpy.ops.object.mode_set(mode='OBJECT')
                recipient.select_set(True)
                bpy.context.view_layer.objects.active = recipient
                bpy.ops.object.mode_set(mode='EDIT')

                # Копируем трансформации костей в Edit Mode
                for donor_bone in donor_armature.data.edit_bones:
                    if donor_bone.name in recipient.data.edit_bones:
                        recipient_bone = recipient.data.edit_bones[donor_bone.name]
                        recipient_bone.head = donor_bone.head
                        recipient_bone.tail = donor_bone.tail
                        recipient_bone.roll = donor_bone.roll

        # Возвращаемся в исходный режим
        bpy.ops.object.mode_set(mode='OBJECT')

        self.report({'INFO'}, "Bone transforms copied successfully in Edit Mode.")
        return {'FINISHED'}

# Operator to clean up bone influences on vertices (max influences check)
class CleanUpBoneInfluencesOperator(bpy.types.Operator):
    """Clean up vertices with more than the specified number of bone influences"""
    bl_idname = "object.clean_up_bone_influences"
    bl_label = "Clean Up Bone Influences"
    bl_options = {'REGISTER', 'UNDO'}

    max_influences: IntProperty(
        name="Max Influences",
        description="Maximum number of bone influences per vertex",
        default=3,
        min=1,
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH' and context.mode == 'EDIT_MESH'

    def execute(self, context):
        obj = context.active_object

        # Ensure we're in Object Mode
        current_mode = obj.mode
        if current_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        mesh = obj.data
        vgroups = obj.vertex_groups

        if not vgroups:
            self.report({'WARNING'}, "Object has no vertex groups")
            return {'CANCELLED'}

        num_weights_removed = 0
        num_vertices_adjusted = 0

        for vert in mesh.vertices:
            # Get all groups and weights for this vertex
            weights = []
            for g in vert.groups:
                group = vgroups[g.group]
                weight = g.weight
                weights.append((group, weight))

            # Sort weights in descending order
            weights.sort(key=lambda x: x[1], reverse=True)

            if len(weights) > self.max_influences:
                # Remove the smallest weights to limit max influences
                for group, weight in weights[self.max_influences:]:
                    group.remove([vert.index])
                    num_weights_removed += 1
                num_vertices_adjusted += 1

            # Normalize remaining weights
            total_weight = sum(w[1] for w in weights[:self.max_influences])
            if total_weight > 0:
                for group, weight in weights[:self.max_influences]:
                    group.add([vert.index], weight / total_weight, 'REPLACE')

        self.report({'INFO'}, f"Removed {num_weights_removed} weights; adjusted {num_vertices_adjusted} vertices to have max {self.max_influences} influences")
        return {'FINISHED'}

# Operator to clean up weights below a threshold and normalize
class CleanUpWeightsThresholdOperator(bpy.types.Operator):
    """Clean up weights below a threshold and normalize the remaining weights"""
    bl_idname = "object.clean_up_weights_threshold"
    bl_label = "Clean Up Weights by Threshold"
    bl_options = {'REGISTER', 'UNDO'}

    threshold: FloatProperty(
        name="Threshold",
        description="Weights below this value will be removed",
        default=0.050,
        min=0.0,
        max=1.0,
    )

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'MESH'

    def execute(self, context):
        obj = context.active_object

        # Ensure we're in Object Mode
        current_mode = obj.mode
        if current_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        mesh = obj.data
        vgroups = obj.vertex_groups

        if not vgroups:
            self.report({'WARNING'}, "Object has no vertex groups")
            return {'CANCELLED'}

        num_weights_removed = 0

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

            # Normalize remaining weights
            total_weight = sum(w[1] for w in weights)
            if total_weight > 0:
                for group, weight in weights:
                    group.add([vert.index], weight / total_weight, 'REPLACE')

        self.report({'INFO'}, f"Removed {num_weights_removed} weights below {self.threshold:.3f}")
        return {'FINISHED'}


# Operator to smooth selected vertices weights
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

# Panel for UI - Tech Anim Tools
class TechAnimToolsPanel(bpy.types.Panel):
    bl_label = "Tech Anim Tools"
    bl_idname = "OBJECT_PT_techanim_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tech Anim Tools'

    def draw(self, context):
        layout = self.layout
        col = layout.column()

        # Section for bone transforms in Edit Mode
        col.label(text="Bone Transforms (Edit Mode):")
        col.operator("object.copy_bones_transforms_edit_mode", text="Copy Bones Transforms (Edit Mode)")

        col.separator()

        # Section for Constraints
        col.label(text="Constraints:")
        col.operator("object.create_constraints", text="Create Constraints")
        col.operator("object.remove_constraints", text="Remove Constraints")

        col.separator()

        # Section for Vertex Weights Tools (Edit Mode)
        if context.mode == 'EDIT_MESH' and context.active_object and context.active_object.type == 'MESH':  # Check for Edit Mode and Mesh
            col.label(text="Vertex Weights Tools:")
            col.operator("object.clean_up_bone_influences", text="Clean Up Bone Influences")
            col.operator("object.clean_up_weights_threshold", text="Clean Up Weights by Threshold")
            col.operator("object.smooth_selected_vertices_weights", text="Smooth Selected Vertices Weights")


# Panel for UI - Item Tab (for vertex weight operations)
class ItemWeightToolsPanel(bpy.types.Panel):
    bl_label = "Vertex Weight Tools"
    bl_idname = "MESH_PT_vertex_weight_tools"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    bl_category = 'Item'

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.mode == 'EDIT_MESH'

    def draw(self, context):
        layout = self.layout
        col = layout.column()

        # Adding buttons for operators related to vertex weights
        col.operator("object.clean_up_bone_influences", text="Clean Up Bone Influences")
        col.operator("object.clean_up_weights_threshold", text="Clean Up Weights by Threshold")
        col.operator("object.smooth_selected_vertices_weights", text="Smooth Selected Vertices Weights")

# Registration functions
def register():
    bpy.utils.register_class(CopyBonesTransformsEditModeOperator)
    bpy.utils.register_class(CreateConstraintsOperator)
    bpy.utils.register_class(RemoveConstraintsOperator)
    bpy.utils.register_class(CleanUpBoneInfluencesOperator)
    bpy.utils.register_class(CleanUpWeightsThresholdOperator)
    bpy.utils.register_class(SmoothSelectedVerticesWeightsOperator)
    bpy.utils.register_class(TechAnimToolsPanel)
    bpy.utils.register_class(ItemWeightToolsPanel)

def unregister():
    bpy.utils.unregister_class(CopyBonesTransformsEditModeOperator)
    bpy.utils.unregister_class(CreateConstraintsOperator)
    bpy.utils.unregister_class(RemoveConstraintsOperator)
    bpy.utils.unregister_class(CleanUpBoneInfluencesOperator)
    bpy.utils.unregister_class(CleanUpWeightsThresholdOperator)
    bpy.utils.unregister_class(SmoothSelectedVerticesWeightsOperator)
    bpy.utils.unregister_class(TechAnimToolsPanel)
    bpy.utils.unregister_class(ItemWeightToolsPanel)



if __name__ == "__main__":
    register()