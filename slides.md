
# White

* Pipline initiation
pipeline_init
QueryAnnotator

                
* Orbbec RGB-D collection reader
CollectionReaderAnnotator(descriptor=tracy_config)

* Image and point-cloud preprocessing
ImagePreprocessorAnnotator

* Point-cloud cropping
PointcloudCropAnnotator

* Supporting-plane detection
PlaneAnnotator

* Above-plane cluster extraction
PointCloudClusterExtractor

* PCA-based pose estimation
ClusterPosePCAAnnotator

* cluster color annotation
ClusterColorAnnotator

* ROS 2 query result generation
GenerateQueryResult

## Observed behavior

The pipeline demonstrated the complete path from RGB-D acquisition to object
hypotheses with pose and color information.  

The pipline was falsly ditecting large box of grey and white(for reflective areas) of the table.
While missing requested colored cubes.

# Blue

* Pipline initiation
pipeline_init
QueryAnnotator

                
* Orbbec RGB-D collection reader
CollectionReaderAnnotator(descriptor=tracy_config)

* Image and point-cloud preprocessing
ImagePreprocessorAnnotator

* query-selected HSV segmentation
* largest matching image contour
ImageClusterExtractor

* corresponding 3D points from depth data
* bounding-box pose and size estimation


* ROS 2 query result generation
GenerateQueryResult

## Observed behavior

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
    -> pipeline initialization
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


## mcap_recorder

The recorder follows one high-level sequence:

1. **Configuration** defines the ROS topics, output directory, MCAP storage
   preset, and recorder node name.

2. **Setup** verifies that the destination does not already exist and prepares
   its parent directory. This protects earlier recordings from accidental
   overwrite before any subscriptions are started.
   
3. **Create recorder backend** builds the rosbag storage and recording options,
   checks that an MCAP writer is available, and creates the concrete recorder.

4. **Continuous recording** starts topic discovery and message processing before
   starting the writer. The backend then captures the configured ROS messages
   continuously rather than waiting for behavior-tree ticks.
5. **Status updates** occur whenever RoboKudo ticks the annotator. Each update
   confirms that recording is active, reports the destination, and returns
   `Status.SUCCESS`; 
6. **Shutdown and finalization** stops recording before stopping topic discovery
   and spinning, then releases the backend. 
   


### Observed behavior

The analysis engine successfully recorded the configured sensor stream to an
MCAP bag. The recorded data was also replayed successfully.

Many later experimantations was done using the data stored next cloud using storage red.

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
