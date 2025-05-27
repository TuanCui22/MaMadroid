# MaMaDroid (Updated Version)

**MaMaDroid** is a machine learning-based Android malware detection system originally introduced in the NDSS 2017 paper.  
This version has been completely updated and refactored to work with modern Python environments and tooling.

## 🔧 Key Updates

- ✅ Migrated to Python 3
- ✅ Refactored and cleaned up the original codebase
- ✅ Updated all dependencies to latest compatible versions
- ✅ Improved overall compatibility and stability

---

## 📦 Features

- Extracts API call sequences from APK files
- Constructs behavioral models using Markov chains
- Classifies Android apps as benign or malicious
- Supports family-based, package-based, and class-based analysis modes

---

## ⚙️ Installation

Make sure `apktool`, `Java`, and `androguard` are installed.

```bash
git clone https://github.com/TuanCui22/MaMadroid.git
cd MaMadroid
pip install -r requirements.txt
````

---

## 🚀 Usage

```bash
python mamadroid.py -i /path/to/apk/ -o output_dir/ -m family
```

| Option | Description                                    |
| ------ | ---------------------------------------------- |
| `-i`   | Path to the input directory with APK files     |
| `-o`   | Path to the output directory                   |
| `-m`   | Modeling mode: `family`, `package`, or `class` |

---

## 🧠 Based On

> MaMaDroid: Detecting Android Malware by Building Markov Chains of Behavioral Models
> *Mariano Graziano, Davide Canali, Leyla Bilge, Ashwin Rao, and Davide Balzarotti*
> NDSS 2017
> [Read the paper](https://www.ndss-symposium.org/ndss2017/ndss-2017-programme/mamadroid-detecting-android-malware-building-markov-chains-behavioral-models/)

---

## 📜 License

This project is intended for academic and research purposes only.

---

```

---

### 🧾 GitHub Repository Description (short, for the repo)

> A refactored and modernized version of MaMaDroid, a machine learning-based Android malware detection tool using behavioral modeling and Markov chains.
