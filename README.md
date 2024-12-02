# Moomins API

![Project Status](https://img.shields.io/badge/status-active-green)


### Demo Reels
[@Moomins Pipeline Team Channel](https://www.youtube.com/@NFXMoomins2024/videos)
| Pipeline   | Step        | Video Links                                
|--------|-------------|---------------------------------------------
| Asset   | Lookdev Dept      | [@Video](https://youtu.be/0P0iHkYt0OI?si=HCn1jY91y8nt1T0w)
| Shot    | Kim Dami      | [@Video](https://youtu.be/_bSvw0jTWvc?si=bVcHb_R883TwFA4b)
| Shot    | Park Han Byeol      | [@Video](https://youtu.be/WVaZMLCwjKs?si=Hqx80I_eaoCdn7eo)
| Shot    | Park Ju Seok      | [@Video](https://youtu.be/hPuDBoU4WeQ?si=SOlPmenjOTkBYTxJ)


### Project Overview
**Project Name**: Moomins API  
**Development Period**: 2024.08.13 - 2024.09.05  
**Team Name**: Moomins  
**Operating System**: Linux  
**Programming Language**: Python3  
**Software Used**: 
- Vs Code
- Maya
- Nuke
- Shotgun
- FFmpeg
- Qt Designer
- Adobe Premiere Pro
- Adobe Illustrator
- Adobe Express
- ideogram.ai

### Concept
In the VFX production environment, artists often face decreased productivity and increased fatigue due to the complexities of setting up workflows and managing files. **Moomins API** was developed to address these issues by providing an automation tool that integrates with Shotgun, significantly reducing project setup time and improving convenience. The goal is to create a more comfortable work environment for artists, enabling them to work more effectively and efficiently.

### Goals
- **Project Setup Automation**: Reduce the time required for artists to set up projects.
- **Integration with Shotgun**: Enhance the efficiency of project management.
- **Maximize Workflow Efficiency**: Provide an environment where artists can focus on creative work.

### **Shotgun Workflow Automation**
- **Task and Status Auto-Sync**: Automatically sync assigned tasks and statuses with the Shotgun database in real-time to ensure up-to-date information.
- **Real-Time Data Integration**: Reflect progress accurately with real-time updates from the Shotgun database.
- **Version Control Integration**: Simplify version management by integrating it into the loader through right-click options.
- **Automatic File and Folder Creation**: Automate the creation of files and folders upon program execution, including updates to the Shotgun database for efficient workflow management.

## Development Period
- **Start Date**: 2024-08-13  
- **End Date**: 2024-09-05
- **Trimming**: 2024-11

## Team Members
| Role   | Name        | GitHub Profile                                
|--------|-------------|---------------------------------------------
| Team Leader   | Seo Hyo Eun      | [@shienasnow](https://github.com/shienasnow)
| Team Member   | Kim Dami      | 
| Team Member   | Park Han Byeol      | 
| Team Member   | Park Ju Seok      | [@ParkHashhh](https://github.com/ParkHashhh)
| Team Member   | Yeom Jung Hyun      | [@yyyjh1213](https://github.com/yyyjh1213)

## Project Structure
```plaintext
Moomins-API/
├── api_scripts/
│   ├── maya_api.py             # Modules related to maya.cmds
│   ├── nuke_api.py             # Modules related to Nuke API
│   ├── shotgun_api.py          # Modules related to Shotgun API
│   └── capturecode.py          # Capture module
├── core/                       # Static files (images, icons, etc.)
│   ├── login/                  # Login interface
│   ├── asset_maya/             # Maya pipeline for asset work
│   ├── shot_maya/              # Maya pipeline for shot work
│   └── nuke/                   # Nuke pipeline for shot work
├── sourceimages                # Collection of source images (PNG)
└── create_desktop_file.py      # Execution file
```

### Required Packages
The list of external packages required to run this API is described in requirements.txt.

"pip install -r requirements.txt"
You can install the required libraries with the above commands.
