# Acrambly: Perception

## Mid-term Presentation

Oct 2 2026

Nasim

> TODO: Add project motivation.

## `preception_pipline1.py`

### Role

It is a general tabletop-perception analysis engine for RoboKudo. 

The approach is primarily geometry-driven.  By using rgbd sensor data it first finds
the table plane in the point cloud and then searches for distinct three-
dimensional clusters above that plane.


### Processing flow

```text
ROS 2 query
    -> pipeline initialization
    -> Orbbec RGB-D collection reader
    -> image and point-cloud preprocessing
    -> point-cloud cropping
    -> supporting-plane detection
    -> above-plane cluster extraction
    -> PCA-based pose estimation
    -> cluster color annotation
    -> ROS 2 query result generation
```

1. `pipeline_init()` prepares the RoboKudo pipeline and its common analysis
   state.
2. `QueryAnnotator` receives a query containing the requested object type and
   color. waits for a perception request received through the
   RoboKudo query action.
3. `CollectionReaderAnnotator` obtains synchronized sensor data using the
   `orbbec` descriptor.
4. `ImagePreprocessorAnnotator` prepares the RGB image, depth image, and point
   cloud needed by the following annotators.
5. `PointcloudCropAnnotator` restricts processing to the relevant workspace.
   Removing irrelevant points reduces the data passed to plane and cluster
   detection.
6. `PlaneAnnotator` finds the dominant supporting plane. In the tabletop
   scenario, this plane represents the table surface. It uses RANSAC to fit the
   current point cloud, without a trained model.
7. `PointCloudClusterExtractor` uses DBSCAN, an unsupervised clustering method,
   to group points above the plane into separate object hypotheses.
8. `ClusterPosePCAAnnotator` applies principal component analysis, an
   unsupervised statistical method, to estimate a pose from each cluster's
   spatial distribution.
9. `ClusterColorAnnotator` adds semantic color information to the detected
   clusters using color rules rather than a trained classifier.
10. `GenerateQueryResult` converts the resulting object hypotheses into the
    ROS message format and sends the action result.

No deep-learning model is used in this pipeline.


### Observed behavior

The pipeline demonstrated the complete path from RGB-D acquisition to object
hypotheses with pose and color information.  

the pipline was ditecting large box of grey and white(for reflective areas) of the table, some times those boxes also contain the cuebs but the pipline still takes the colur of the ditected cluster as gray or white as large portion is white or gray.


## `preception_pipline2.py`

### Role

This file defines a specialized perception pipeline for a single queried
colored cube. 

The query is used as an input to segmentation, allowing the pipeline to
  concentrate on the requested color instead of processing every geometric
  cluster in the scene.


### Processing flow

```text
ROS 2 colored-block query
    -> pipeline initialization
    -> Orbbec RGB-D collection reader
    -> image and point-cloud preprocessing
    -> query-selected HSV segmentation
    -> largest matching image contour
    -> corresponding 3D points from depth data
    -> bounding-box pose and size estimation
    -> ROS 2 query result generation
```

1. `create_color_cluster_descriptor()` defines the supported color names and
   their  HSV ranges.

4. `ImageClusterExtractor` reads the requested color and applies the matching
   HSV range. It retains one matching object, which is appropriate for a query
   requesting one target cube. 

6. `ClusterPoseBBAnnotator` fits an oriented bounding box and derives the
   object's position, orientation, and dimensions through geometric fitting,
   without a learned model.  
7. `GenerateQueryResult` converts the resulting object hypothesis into the ROS
   message format and sends the action result.


### Observed behavior

In the performed demonstrations, this pipeline reliably detected the queried
colored cube and returned its bounding-box pose. 

It precisly ditect even the pose of smaller cubes.

It provided the perception
output required by the subsequent CRAM/Coraplex integration. 

## Storage Red

Motivation: In the environment with a newer Linux kernel used for
this project, the original robokudo MongoDB recording workflow encountered 
a compatibility problem. 

A dedicated RoboKudo analysis engine  with a new caustom annoaor mcap recorder
for recording the sensor input needed to reproduce a perception run. 


### Comparison with the previous `storage.py`


| Aspect | Previous `storage.py` | New `storage_red.py` |
| --- | --- | --- |
| Storage backend | MongoDB through `StorageWriter` | ROS 2 rosbag2 with MCAP through `McapRecorderAnnotator` |
| Data saved | Processed CAS data, views, and world model state | Original RGB-D, camera-info, and transform ROS messages |
| Recording behavior | Writes the current CAS when the pipeline ticks | Records subscribed ROS topics continuously while the pipeline runs |
| Replay input | MongoDB records read back into a CAS | MCAP bag replayed as sensor topics |
| Advantage | More compressed| Easier Implimentation|


### Processing flow

```text
       pipeline initialization
    -> Orbbec RGB-D collection reader
    -> image and point-cloud preprocessing
    -> direct recording of configured ROS topics to MCAP
```

### Recorded topics

| Topic source | Recorded information | Purpose during replay |
| --- | --- | --- |
| Orbbec depth topic | Depth image | Reconstruct three-dimensional scene data |
| Orbbec color topic | RGB image | Run color-based image processing |
| Orbbec camera-info topic | Camera calibration | Interpret and project image measurements |
| `/tf_static` | Static transforms | Recover fixed sensor-frame relationships |

/tf_static is enough only if the complete path from the camera frame to map is fixed


## mcap_recorder

The recorder follows one high-level sequence:

[Open the interactive MCAP recorder workflow](./mcap_recorder_workflow.html).

1. **Configuration** defines the ROS topics, output directory, MCAP storage
   preset, and recorder node name.
**configuration is preparation for the recorder’s lifecycle, rather than a separate lifecycle callback**

2. **Setup** verifies that the destination does not already exist and prepares
   its parent directory. This protects earlier recordings from accidental
   overwrite before any subscriptions are started.
   
3. **Create recorder backend** builds the rosbag storage and recording options,
   checks that an MCAP writer is available, and creates the concrete recorder.

4. **Continuous recording** The backend then captures the configured ROS messages
   continuously rather than waiting for behavior-tree ticks.
5. **Status updates** occur whenever behavior-tree ticks the annotator. Each update
   confirms that recording is active, reports the destination.
6. **Shutdown and finalization** stops recording before stopping topic discovery
   and spinning, then releases the backend. The
ordered, idempotent shutdown protects buffered data while allowing both explicit
cleanup and the ROS shutdown callback to finalize the same recorder safely.


### Observed behavior

The analysis engine successfully recorded the configured sensor stream to an
MCAP bag. The recorded data was also replayed successfully.

The team was Also using the data stored next cloud in this way for later experimentions.

show the replay in lap top.


# CRAM and Robokudo Integration V1 (without SemDtSync)

The integration code connects the perception result to the block-stacking
task through the `/robokudo/query` ROS 2 action.

```text
Main steps: 
    -> request block pose through `/robokudo/query`
    -> RoboKudo runs the colored-cube perception pipeline
    -> receive pose
    -> associate the result with the requested color
    -> provide the resulting block poses to the Coraplex task as python dict of str and tuple
```

In white All blocks pose are estimated at the same time and in one preception pipline run.

In Blue Each ROS action goal has object type `block` and exactly one requested
color. Colors that were already found are retained, while missing colors are
queried again using a fresh perception result, up to the configured attempt
limit.

The action-future handling supports both a standalone ROS node and a node that
is already managed by an executor. This keeps the perception query usable alone and 
inside the larger CRAM/Coraplex execution context.
