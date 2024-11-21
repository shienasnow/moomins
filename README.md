# Moomins API

![Project Status](https://img.shields.io/badge/status-active-green)

## Project Overview

**프로젝트 이름**: Moomins API  
**개발 기간**: 2024.08.13 - 2024.09.05  
**팀 이름**: Moomins  
**사용 OS**: Linux  
**사용 언어**: Python3
**사용한 프로그램**: 
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
VFX 제작 환경에서 아티스트들은 복잡한 작업 환경 구축과 파일 관리로 인해 생산성이 저하되고 피로가 증가하고 있습니다. **Moomins API**는 이러한 문제를 해결하기 위해 개발된 자동화 도구로, Shotgun과 연동하여 아티스트의 프로젝트 셋업 시간을 크게 단축시키고 작업의 편의성을 높이는 것을 목표로 합니다. 이를 통해 아티스트들에게 더 편안한 작업 환경을 제공하고, 더욱 효과적으로 작업할 수 있도록 지원합니다.

### Goals
- **프로젝트 셋업 자동화**: 아티스트의 셋업 시간 단축
- **Shotgun과 연동**: 프로젝트 관리 효율성 향상
- **작업 효율성 극대화**: 창의적 작업에 집중할 수 있는 환경 제공

## Key Features

### **Shotgun 연동 자동화**
- **작업 및 Status 자동 동기화**: 할당된 작업과 Status를 Shotgun DB와 실시간으로 동기화하여 항상 최신 정보를 유지합니다.
- **실시간 데이터 연동**: Shotgun DB와의 실시간 연동으로 작업 진행 상황을 정확히 반영합니다.

### **워크플로우 자동화**
- **버전 관리 통합**: Loader 내의 우클릭 기능을 통해 버전 관리 시스템을 통합하여 버전 관리 용이합니다.
- **파일 및 폴더 자동 생성**: 프로그램 실행 시 파일 및 폴더 생성을 자동화하고, Shotgun DB 업데이트를 포함하여 전체 워크플로우를 효율적으로 관리합니다.



## Development Period
- **Start Date**: 2024-08-13
- **End Date**: 2024-09-05

## Team Members
| Role   | Name        | GitHub Profile                                
|--------|-------------|---------------------------------------------
| 팀장   | 설효은      | [@shienasnow](https://github.com/shienasnow)
| 팀원   | 김다미      | 
| 팀원   | 박한별      | 
| 팀원   | 박주석      | [@ParkHashhh](https://github.com/ParkHashhh)
| 팀원   | 염정현      | [@yyyjh1213](https://github.com/yyyjh1213)

## Project Structure
```plaintext
Moomins-API/
├── api_scripts/
│   ├── maya_api.py             # maya.cmds 관련 모듈
│   ├── nuke_api.py             # 누크 api 관련 모듈
│   ├── shotgun_api.py          # 샷그리드 api 관련 모듈
│   └── capturecode.py          # 캡처 모듈
├── core/                       # 정적 파일 (이미지, 아이콘 등)
│   ├── login/                  # 로그인
│   ├── asset_maya/             # 에셋 작업용 마야 파이프라인
│   ├── shot_maya/              # 샷 작업용 마야 파이프라인
│   └── nuke/                   # 샷 작업용 누크 파이프라인
├── sourceimages                # 소스 이미지 png 모음
└── create_desktop_file.py      # 실행 파일
