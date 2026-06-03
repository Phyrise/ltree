# **🌳 ltree**

A lightweight and fast alternative to the standard tree command, tailored specifically for medical imaging datasets (.nii.gz, .nii, .mha).

Standard terminal trees clutter when parsing large medical repositories containing hundreds of repetitive patient slices or volume sequences. ltree clusters homogeneous sibling directories into streamlined, single-line summaries while automatically rendering dataset shape, spacing, and data-type fingerprints.

## **Requirements**

```
Python >= 3.8
SimpleITK >= 2.0.0
NumPy >= 1.20.0
tqdm >= 4.0.0
```

## **Installation**

```
pip install git+\[https://github.com/Phyrise/ltree\](https://github.com/Phyrise/ltree)
```

## **Usage**

``` 
ltree [PATH] [FLAGS]
```
* **PATH** *(Optional)*: Target directory to analyze. Defaults to the current directory (.).  
* **\-s, \--scan**: Skips the directory tree rendering and launches a multi-processed snapshot scan across all volumes to isolate min/median/max shape and spacing configurations.  
* **\-a, \--all**: Forces the directory engine to display hidden files, and local cache paths

## **Example on SynthRAD2023 dataset**

### **1\. Dataset summary tree**

```
ltree synthRAD2023/pelvis

Summary tree for: /export/work/users/arthur/datasets/synthRAD2023/pelvis  
├── 📂 ct (0 dirs, 180 files)  
│   └── [1PA001.nii.gz ... 1PC098.nii.gz (180 files)] 🔍 1PA001.nii.gz -> (565, 338, 146), Spacing: [1.0, 1.0, 2.5], 32-bit float  
├── 📂 mask (0 dirs, 180 files)  
│   └── [1PA001.nii.gz ... 1PC098.nii.gz (180 files)] 🔍 1PA001.nii.gz -> (565, 338, 146), Spacing: [1.0, 1.0, 2.5], 8-bit unsigned integer  
├── 📂 mr (0 dirs, 180 files)  
│   └── [1PA001.nii.gz ... 1PC098.nii.gz (180 files)] 🔍 1PA001.nii.gz -> (565, 338, 146), Spacing: [1.0, 1.0, 2.5], 32-bit float  
└── 📂 overview (0 dirs, 181 files)  
    └── [1PA001\_train.png ... 1\_pelvis\_train.xlsx (181 files)]
```
### **2\. Dataset fingerprint scan**

```
ltree synthRAD2023/pelvis -s

📊 Dataset Fingerprint (540 volumes)  
  • Types:    {'32-bit float': 360, '8-bit unsigned integer': 180}  
  • Shapes:   [390-586; 248-410; 84-153] | Median: [448, 294, 119]  
  • Spacing:  [1.0-1.0; 1.0-1.0; 2.5-2.5] | Median: [1.0, 1.0, 2.5]  
```
