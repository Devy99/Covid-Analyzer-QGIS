<h3 align="center">Covid-Analyzer-QGIS</h3>

  <p align="center">
    A QGIS plugin for tracking Covid-19 cases in Italy
  </p>


<!-- TABLE OF CONTENTS -->
<details open="open">
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

This plugin was created by Devy99 and onairam-97 as a university exam in order to make possible to analyze the Covid-19 pandemic situation in our fatherland, Italy.

### Built With

The plugin is written in Python, with the usage of:
* [PyQGIS](https://docs.qgis.org/3.16/en/docs/pyqgis_developer_cookbook/index.html)
* [PyQT5](https://www.riverbankcomputing.com/static/Docs/PyQt5/)


<!-- GETTING STARTED -->
## Getting Started

Here you will find the istruction for downloading our plugin.

### Prerequisites

In order to download the necessary files, you should have [Git](https://git-scm.com/) on your computer and, of course, [QGIS](https://www.qgis.org/en/site/) where the plugin will be configured.

### Installation

1. Open QGIS and click on Settings > User Profiles > Open active profile folder.
2. Go to python > plugins. This is the folder where all QGIS plugin are stored.
3. Copy the path of this folder and navigate there from the terminal (e.g. cd path/to/folder ).
4. Clone the repo
   ```sh
   git clone https://github.com/Devy99/Covid-Analyzer-QGIS.git
   ```
5. Now reload QGIS window and activate plugin clicking Plugin > Manage and Install Plugins. Then on Installed section, click on Covid Analyzer plugin and then activate it.