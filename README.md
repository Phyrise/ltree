# 🌳 ltree-3d

A lightweight, lightning-fast alternative to the standard `tree` command tailored specifically for **3D Medical Imaging and Machine Learning Datasets** (`.nii.gz`, `.nii`, `.mha`).

Standard terminal trees fall apart when parsing large medical repositories due to hundreds of repetitive patient slice/volume sequences. `ltree` solves this by clustering homogeneous sibling directories into streamlined, single-line summaries while automatically rendering layout fingerprints of your data.

## 🚀 Installation

### Local Development Install (Recommended)
Clone your repository and install it locally in editable mode so changes update in real time:
```bash
git clone [https://github.com/yourusername/ltree.git](https://github.com/yourusername/ltree.git)
cd ltree
pip install -e .