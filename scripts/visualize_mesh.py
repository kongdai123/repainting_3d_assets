import sys

import numpy as np
import plotly.graph_objects as go
import trimesh


def visualize(title, path, colab=False):
    mesh = trimesh.load(path)
    vertex_colors = mesh.visual.vertex_colors.astype(
        np.float16 if colab else np.float32
    )
    vertex_colors /= 255.0
    fig = go.Figure(
        data=[
            go.Mesh3d(
                x=mesh.vertices[:, 0],
                y=mesh.vertices[:, 1],
                z=mesh.vertices[:, 2],
                i=mesh.faces[:, 0],
                j=mesh.faces[:, 1],
                k=mesh.faces[:, 2],
                hoverinfo="none",
                flatshading=True,
                vertexcolor=vertex_colors,
                opacity=1.0,
            )
        ],
        layout=dict(
            title=dict(text=title, x=0.5),
            scene=dict(
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                zaxis=dict(visible=False),
                camera=dict(
                    eye=dict(x=1.5, y=0, z=-0.75),
                    up=dict(x=0, y=1, z=0),
                ),
            ),
            margin=dict(t=40, b=10, l=0, r=0),
        ),
    )
    if colab:
        fig.show(renderer="colab")
    else:
        fig.show()


if __name__ == "__main__":
    assert len(sys.argv) >= 2, "Requires path to the model and an optional title"
    path = sys.argv[1]
    title = sys.argv[2] if len(sys.argv) >= 3 else path
    visualize(title, path)
