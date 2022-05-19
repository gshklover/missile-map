# Detailed Implementation Overview

## Privacy
Server must not expose exact data back to the users - if accurate data is exposed, it can be used to track reporters.

# Algorithm

## Sightings

A "sighting" represents a single observation by a given "observer".<br>
A sighting can be represented by a tuple *(latitude, longitude, time, bearing)*.

## Targets

The goal of the algorithm is to identify "targets" where each target is represented by:
* motion start time 
* trajectory path - a set of straight segments between turn points (latitude, longitude)
* speed within given speed limits

## Implementation

**Goal:** Find minimal set of targets & paths that minimize total observation error.

### Possible approaches:
* Identify "temporally-related sightings" as those where *distance/delta_time* fits approximate target speed
  * Relies on some level of accuracy of sighting vs time
* Cluster sightings by proximity to a given segment (start_loc, end_loc, start_time, speed)
  * Can run optimization algorithm to find N-segment paths that maximize sighting match.
  * For example, incrementally, add targets / segments until acceptable accuracy is achieved
* Proximity can be measured as a monotonic function that drops significantly after expected observation radius

Variant: Gaussian Clustering
  * For all pairs of sightings, compute the line passing through the pair
  * Filter out lines that do not fit into single segment model
  * Embed the line parameters into an n-dimensional tuple and cluster tuples
  * Challenges:
    * Slope over pairs of sightings may be very noisy

Variant: Grid
  * Break the area into units of decreasing size.
  * Group sightings over same & neighbouring units

Variant: Expectation Maximization 
* For a given number of segments, run expectation maximization algorithm:
  * Define N random segments
  * Attach sightings to best segment
  * Re-estimate the segment based on attachment
  * Repeat last 2 steps until stop condition is met (improvement, for example)
