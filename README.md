# Moomins API

![Project Status](https://img.shields.io/badge/status-active-green)

## 📋 프로젝트 개요 (Project Overview)

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

### 기획 의도 (Concept)
VFX 제작 환경에서 아티스트들은 복잡한 작업 환경 구축과 파일 관리로 인해 생산성이 저하되고 피로가 증가하고 있습니다. **Moomins API**는 이러한 문제를 해결하기 위해 개발된 자동화 도구로, Shotgun과 연동하여 아티스트의 프로젝트 셋업 시간을 크게 단축시키고 작업의 편의성을 높이는 것을 목표로 합니다. 이를 통해 아티스트들에게 더 편안한 작업 환경을 제공하고, 더욱 효과적으로 작업할 수 있도록 지원합니다.

### 주요 목표 (Goals)
- **프로젝트 셋업 자동화**: 아티스트의 셋업 시간 단축
- **Shotgun과 연동**: 프로젝트 관리 효율성 향상
- **작업 효율성 극대화**: 창의적 작업에 집중할 수 있는 환경 제공

## 🚀 주요 기능 (Key Features)

### 1️⃣ **Shotgun 연동 자동화**
- **작업 및 Status 자동 동기화**: 할당된 작업과 Status를 Shotgun DB와 실시간으로 동기화하여 항상 최신 정보를 유지합니다.
- **실시간 데이터 연동**: Shotgun DB와의 실시간 연동으로 작업 진행 상황을 정확히 반영합니다.

### 2️⃣ **워크플로우 자동화**
- **버전 관리 통합**: Loader 내의 우클릭 기능을 통해 버전 관리 시스템을 통합하여 버전 관리 용이합니다.
- **파일 및 폴더 자동 생성**: 프로그램 실행 시 파일 및 폴더 생성을 자동화하고, Shotgun DB 업데이트를 포함하여 전체 워크플로우를 효율적으로 관리합니다.

### 3️⃣ **사용자 맞춤 인터페이스**
- **로그인 시스템**: 아티스트의 역할에 따라 Asset 작업자와 Shot 작업자로 구분하여 맞춤형 작업 환경을 제공합니다.
- **작업 자동 불러오기**: Task별 최적화된 Loader를 통해 아티스트에게 할당된 작업을 Shotgun을 통해 자동으로 불러와 작업을 시작할 수 있는 기능을 제공합니다.
- **프로그램 내 메뉴 실행**: Maya, Nuke 등 주요 VFX 소프트웨어에 메뉴를 추가하여 프로그램을 실행하고 필요한 작업을 진행할 수 있습니다.
- **파일 접근 용이성**: Import, Upload, Publish 메뉴를 통해 파일 접근과 작업을 간편하게 처리합니다.

### 4️⃣ **직관적인 UI/UX**
- **파일 썸네일 표시**: 현재 작업 중인 파일의 썸네일을 표시하여 시각적으로 작업 내용을 쉽게 확인할 수 있습니다.
- **상태 유기적 변화**: Shotgun과 프로그램 내의 Status를 유기적으로 반영하여 직관적인 사용자 경험을 제공합니다.

## 📅 개발 기간 (Development Period)
- **시작일**: 2024-08-13
- **종료일**: 2024-09-05

## 👥 팀 구성 (Team Members)
| 역할   | 이름        | GitHub 프로필                                
|--------|-------------|---------------------------------------------
| 팀장   | 설효은      | [@shienasnow](https://github.com/shienasnow)
| 팀원   | 김다미      | 
| 팀원   | 박한별      | 
| 팀원   | 박주석      | [@ParkHashhh](https://github.com/ParkHashhh)
| 팀원   | 염정현      | [@yyyjh1213](https://github.com/yyyjh1213)

## 📂 프로젝트 구조 (Project Structure)
```plaintext
Moomins-API/
├── src/                         # 소스 코드
│   ├── automation/              # 자동화 기능 관련 코드
│   ├── integration/             # Shotgun 연동 관련 코드
│   ├── ui/                      # UI 구성 요소
│   └── utils/                   # 유틸리티 함수
├── assets/                      # 정적 파일 (이미지, 아이콘 등)
├── README.md                    # 프로젝트 설명서
└── requirements.txt             # 필수 라이브러리 목록
