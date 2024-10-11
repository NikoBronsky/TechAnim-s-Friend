# TechAnim Friend

## Description

**TechAnim Friend** is a set of tools designed to assist technical animators in Blender. The addon provides the following features:

- **Copy Bone Transforms**:
  - **Copy Bones Transforms**: Copies bone transforms from a donor armature to selected recipient armatures.

- **Create Constraints**:
  - **Create Constraints**: Creates _Copy Transforms_ constraints from the donor armature to selected recipient armatures, simplifying the retargeting process.

- **Remove Constraints**:
  - **Remove Constraints**: Removes the created constraints from selected recipient armatures.

- **Check Weight Amount**:
  - **Check Weight Amount**: Selects vertices that are influenced by more than a specified number of bones. Useful for optimizing skinning.

- **Smooth Selected Vertices Weights**:
  - **Smooth Selected Vertices Weights**: Smooths the weights of selected vertices by averaging them with neighboring vertices, leading to smoother deformations during animation.

## Installation

1. **Save the addon**:
   - Save the addon code to a file with a `.py` extension, e.g., `techanim_friend.py`.

2. **Install the addon in Blender**:
   - Open Blender and go to **Edit > Preferences > Add-ons**.
   - Click **Install...**, select the saved addon file, and install it.
   - In the list of addons, find **TechAnim Friend** and check the box to activate it.

## Usage

1. **Access the tools**:
   - In the 3D Viewport, press `N` to open the sidebar.
   - Navigate to the **Tech Anim Tools** tab.

2. **Using the operators**:
   - **Copy Bones Transforms**: Select the donor armature and recipient armatures. Make the donor armature the active object. Click **Copy Bones Transforms**.
   - **Create Constraints**: Similarly, select the donor armature and recipient armatures. Click **Create Constraints** to create the constraints.
   - **Remove Constraints**: Select the recipient armatures and click **Remove Constraints** to delete the created constraints.
   - **Check Weight Amount**: Select the skinned mesh and make it the active object. Click **Check Weight Amount** and specify the maximum number of influencing bones.
   - **Smooth Selected Vertices Weights**: In **Edit Mode**, select the vertices of the mesh. Click **Smooth Selected Vertices Weights**, specify the number of iterations, and apply the smoothing.

## License

This addon is distributed under the [MIT License](LICENSE).

