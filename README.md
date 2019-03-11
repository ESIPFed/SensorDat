# SensorDat
## Project description:
Real-time sensors are increasingly being used for scientific analysis and discovery in earth science research. The Internet of Things (IoT) concept describes an environment in which small, inexpensive sensors become ubiquitous and stream their data to the Internet in real-time. However, sensors used for scientific research purposes require additional sophistication due to issues surrounding standards and metadata requirements, spatial and temporal coverage, data quality considerations, measurement specifications, and geolocation information. To address the IoT as it could be applied to the geosciences, an NSF-funded project called “Cloud-Hosted Real-time Data Services for the Geosciences” ([CHORDS](http://chordsrt.com)) was proposed and funded in 2016 to explore the use of real-time data in a scientific context. Through the work on this project thus far, it has become clear that many of the needs of NSF-funded measurement teams associated with this project are similar, and therefore could be extended to other scientific domains. In particular, through systems like CHORDS, it is now possible to address data quality issues in real-time so that problems are caught quickly, ultimately improving measurement quality. In addition, metadata standards are evolving to help researchers discover streaming data in their area of interest, and to describe features needed for proper interpretation of the data (e.g., units of measurement, spatial and/or temporal coverage). Through the ESIP lab, we would like to 1) extend the use of CHORDS to real-time data streams that are outside of the traditional NSF Geosciences domain, including new varieties of sensors that take advantage of IoT miniaturization, and 2) develop advanced workflows focused on automated data quality and data quality annotation and/or correction.

## Project objectives, significance and impact: 
Demonstrate cloud-hosted streaming of new real-time data sources outside of typical NSF Geosciences funded teams. This will demonstrate that there are common aspects of real-time data handling that span broad scientific areas. Through this testbed, we would work to build further the community of envirosensing researchers.
Develop a testbed of scripts to assess and identify data quality issues in real-time. This will assist in handling data issues as soon as they appear so that the damage to the resulting dataset is mitigated. This testbed will set the stage for community development of robust production workflows for sensor-based science and cloud-hosted data services.
Develop plans for how we might standardize ways to annotate these data for data quality issues and/or make corrections. Pilot a standard for manual annotations and corrections to sensor data that will allow applications to return a “view” onto the data without modifying the raw sensor data in place. Lack of annotation schemes is currently a huge gap in practice, so this will bolster the provenance of data streams so that limitations and quality issues in a dataset are clearly documented.

## Description of key project steps and timeline: 						
### Summer 2018
Announce the SensorDat lab testbed at the 2018 ESIP Summer Meeting via the EnviroSensing sessions.

### Early Fall 2018
Establish project GitHub repository.
Create ESIP AWS instances of CHORDS in the cloud.
Announce availability via the ESIP newsletter and the EnviroSensing Cluster.
Attach one or more continuous environmental data streams, including from sites associated with the U.S. LTER Network, to ESIP CHORDS instances. 

### Mid-Fall 2018
Develop scripts to tap into data streams, develop basic QC check capability.
Develop requirements, and/or test the performance of more sophisticated anomaly detection techniques.
Develop a plan describing requirements for annotation of data quality issues and/or ways to make corrections through a system like CHORDS.

### Early Winter 2018
Work with new data streams as they become available.
Create a poster for the ESIP Winter Meeting describing lessons learned.

### Late Winter 2018
Code wrap up and documentation.
Complete final report.

