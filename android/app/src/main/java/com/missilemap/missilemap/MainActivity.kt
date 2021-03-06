package com.missilemap.missilemap

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.location.Location
import android.location.LocationManager
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.view.Menu
import android.view.MenuItem
import android.view.View
import android.widget.Button
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import com.android.volley.Request
import com.google.android.gms.maps.*
import com.google.android.gms.maps.model.*
import com.android.volley.RequestQueue
import com.android.volley.toolbox.JsonArrayRequest
import com.android.volley.toolbox.JsonObjectRequest
import com.android.volley.toolbox.Volley
import com.google.android.gms.location.*
import com.google.gson.*
import org.json.JSONObject
import kotlin.math.min


val DEFAULT_ZOOM : Float = 10.0f   // default map zoom
val MAP_UPDATE_RATE_MS : Long = 100     // minimum time (ms) between map updates
val TARGET_UPDATE_RATE_MS : Long = 3000 // minimum time (ms) between polling the server
val POST_URL = "http://10.0.2.2:8000/sightings"
val GET_URL = "http://10.0.2.2:8000/targets"


/**
 * Geo-location
 */
class Point (
    val latitude: Double,
    val longitude: Double
) {}

/**
 * Defines a tracked target
 */
class Target (
    val startTime: Int,
    val speed: Float,
    val path: Array<Point>
) {}

/**
 * Configures a Gson object for REST api handling
 */
fun getGson(): Gson {
    return Gson()
}

/**
 * Main application activity
 */
class MainActivity : AppCompatActivity(), SensorEventListener, OnMapReadyCallback {

    // visual elements:
    private lateinit var mReportButton: Button    // "Report" button
    private lateinit var mMap: GoogleMap          // reference to google map object
    private var mMapPos: Marker? = null           // current position marker on the map
    private var mLastUpdateTime: Long = 0         // last update time mMap
    private var mTargetMarkers : Array<Polyline> = arrayOf() // list of markers used to render targets

    // when "true" shows current map location
    private var showLocation: Boolean = true
        set(value) {
            if (field == value) return

            field = value
            mMapPos = if (value) {
                // create a marker for the center:
                createPositionMarker()
            } else {
                // update orientation to point North:
                if (::mMap.isInitialized) {
                    val currentPos = mMap.cameraPosition
                    val newPos = CameraPosition(
                        currentPos.target,
                        currentPos.zoom,
                        0f,
                        0f
                    )
                    mMap.moveCamera(CameraUpdateFactory.newCameraPosition(newPos))
                }
                mMapPos?.remove()
                null
            }
            updateReportButton()
        }

    // sensor readings:
    private lateinit var mLocationClient: FusedLocationProviderClient // location client
    private lateinit var mLocationCallback: LocationCallback // location callback for FusedLocationClient
    private val mGravity = FloatArray(3) { _ -> 0.0f }      // current accelerometer reading
    private val mGeomagnetic = FloatArray(3) { _ -> 0.0f }  // current magnetic sensor reading
    private var mLocation : Location? = null                     // current location
    private var mBearing : Float = 0f                            // current phone bearing (radians, [-pi..+pi])

    // handling requests:
    private lateinit var mRequestQueue : RequestQueue      // REST request queue
    private lateinit var mUpdateTask : Runnable            // periodic update task

    // model objects:
    private var mTargets : Array<Target> = arrayOf()  // list of known targets

    // called when the activity is first created
    override fun onCreate(savedInstanceState: Bundle?) {
        val parent = this
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        setSupportActionBar(findViewById(R.id.toolbar))

        mReportButton = findViewById<Button>(R.id.report_btn)
        mReportButton.isEnabled = false

        mRequestQueue = Volley.newRequestQueue(this)
        mUpdateTask = Runnable { parent.onUpdate() }

        mLocationClient = LocationServices.getFusedLocationProviderClient(this)
        mLocationCallback = object: LocationCallback() {
            override fun onLocationResult(location: LocationResult) {
                parent.onLocationResult(location)
            }
        }

        // Obtain the SupportMapFragment and get notified when the map is ready to be used.
        val mapFragment = supportFragmentManager.findFragmentById(R.id.map) as SupportMapFragment
        mapFragment.getMapAsync(this)

        // check location permissions and request if missing:
        if (ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION ) != PackageManager.PERMISSION_GRANTED &&
            ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_COARSE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this, arrayOf(Manifest.permission.ACCESS_FINE_LOCATION), 200)
        }
    }

    // called when main activity moves to foreground
    override fun onResume() {
        super.onResume()

        // initialize magnetic field sensor
        val sensorManager = getSystemService(SENSOR_SERVICE) as SensorManager
        val sensorAccel = sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)
        val sensorMagnetic = sensorManager.getDefaultSensor(Sensor.TYPE_MAGNETIC_FIELD)
        sensorManager.registerListener(this, sensorAccel, SensorManager.SENSOR_DELAY_NORMAL)
        sensorManager.registerListener(this, sensorMagnetic, SensorManager.SENSOR_DELAY_NORMAL)

        requestLocation()
        scheduleUpdate()
    }

    // called when main activity is paused (no in foreground)
    override fun onPause() {
        super.onPause()

        val sensorManager = getSystemService(Context.SENSOR_SERVICE) as SensorManager
        sensorManager.unregisterListener(this)

        mLocationClient.removeLocationUpdates(mLocationCallback)

        Handler(Looper.getMainLooper()).removeCallbacks(mUpdateTask)
    }

    // called to populate options menu
    override fun onCreateOptionsMenu(menu: Menu): Boolean {
        menuInflater.inflate(R.menu.menu_main, menu)
        return true;
    }

    // called to handle a menu actions
    override fun onOptionsItemSelected(item: MenuItem): Boolean {
        when (item.itemId) {
            R.id.action_showmap -> {
                // toggle between showing a map vs showing the current location
                showLocation = !showLocation
                return true
            }
            else -> {
                return super.onOptionsItemSelected(item)
            }
        }
    }

    // called by LocationManager when location changes
    fun onLocationResult(location: LocationResult) {
        mLocation = location.lastLocation
//        mLocation = Location(LocationManager.GPS_PROVIDER)
//        mLocation?.latitude = 47.487079766379715
//        mLocation?.longitude = 33.081535775384715
        updateMapPos()
        updateReportButton()
    }

    // called by permissions manager to process permission change request
    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        // check if granted ACCESS_FINE_LOCATION
        when (requestCode) {
            200 -> {
                if (grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                    requestLocation()
                }
            }
        }
    }

    // requests current location updates
    private fun requestLocation() {
        if (
            ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED ||
            ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED
        ) {
            val locationRequest = LocationRequest.create()
            locationRequest.interval = 1000
            locationRequest.priority = LocationRequest.PRIORITY_HIGH_ACCURACY
            mLocationClient.requestLocationUpdates(locationRequest, mLocationCallback, Looper.getMainLooper())

//            val locationManager = getSystemService(Context.LOCATION_SERVICE) as LocationManager
//            locationManager.requestLocationUpdates(LocationManager.GPS_PROVIDER, 0, 0.1f, this)
        }
    }

    // called when one of the sensors (magnetic/accelerometer) changes
    override fun onSensorChanged(sensorEvent: SensorEvent?) {
        when (sensorEvent?.sensor?.type) {
            Sensor.TYPE_ACCELEROMETER -> {
                mGravity[0] = sensorEvent.values[0]
                mGravity[1] = sensorEvent.values[1]
                mGravity[2] = sensorEvent.values[2]
            }
            Sensor.TYPE_MAGNETIC_FIELD -> {
                mGeomagnetic[0] = sensorEvent.values[0]
                mGeomagnetic[1] = sensorEvent.values[1]
                mGeomagnetic[2] = sensorEvent.values[2]
            }
            else -> return
        }
        updatedOrientation()
    }

    // update orientation based on sensor data
    private fun updatedOrientation() {
        val rotation = FloatArray(9)

        if (SensorManager.getRotationMatrix(rotation, null, mGravity, mGeomagnetic)) {
            val orientation = FloatArray(3)
            SensorManager.getOrientation(rotation, orientation)

            // sensors are noisy. we are using exponential moving average to smooth out the reading.
            val alpha = 0.9f
            var bearing = orientation[0]
            val pi = Math.PI.toFloat()
            if (Math.abs(mBearing - bearing) > pi) {
                // wrap around, choose shortest pass
                if (bearing > 0) {
                    bearing -= 2f * pi
                } else {
                    bearing += 2f * pi
                }
            }
            mBearing = alpha * mBearing  + (1 - alpha) * bearing
            if (mBearing < -pi) {
                mBearing += 2 * pi
            } else if (mBearing > pi) {
                mBearing -= 2 * pi
            }
            updateMapPos()
        }
    }

    // not used
    override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {}

    // update current map position
    private fun updateMapPos() {
        val longitude = mLocation?.longitude
        val latitude = mLocation?.latitude

        if (::mMap.isInitialized && latitude != null && longitude != null) {
            val currentTime = System.currentTimeMillis()
            if (currentTime < mLastUpdateTime || currentTime > mLastUpdateTime + MAP_UPDATE_RATE_MS) {
                mLastUpdateTime = currentTime
                if (showLocation) {
                    val currentPos = mMap.cameraPosition
                    val newPos = CameraPosition(
                        LatLng(latitude, longitude),
                        currentPos.zoom,
                        0f,
                        Math.toDegrees(mBearing.toDouble()).toFloat()
                    )
                    mMap.moveCamera(CameraUpdateFactory.newCameraPosition(newPos))
                    mMapPos?.position = LatLng(latitude, longitude)
                }
            }
        }
    }

    // update list of targets
    private fun updateTargets(targets: Array<Target>) {
        mTargets = targets

        // clear markers
        for (m in mTargetMarkers) {
            m.remove()
        }
        mTargetMarkers = arrayOf()

        if (::mMap.isInitialized) {
            // remove / update markers on the map
            val polylines = mutableListOf<Polyline>()

            for (t in targets) {
                polylines.add(mMap.addPolyline(
                    PolylineOptions()
                    .color(Color.RED)
                    .width(5f)
                    .addAll( t.path.map { p -> LatLng(p.latitude, p.longitude) }
                )))
            }

            mTargetMarkers = polylines.toTypedArray()
        }
    }

    // called when the GoogleMap object is ready
    override fun onMapReady(googleMap: GoogleMap) {
        mMap = googleMap

        var location = mLocation
        if (location == null) {
            location = Location(LocationManager.GPS_PROVIDER)
            location.latitude = 34.0
            location.longitude = 47.0
        }

        if (showLocation) {
            mMapPos = createPositionMarker()
        }
        mMap.moveCamera(CameraUpdateFactory.newLatLngZoom(LatLng(location.latitude, location.longitude), DEFAULT_ZOOM));

        scheduleUpdate()
    }

    // create center position marker
    private fun createPositionMarker(): Marker? {
        val location = mLocation ?: Location(LocationManager.GPS_PROVIDER)
        val markerSize = defaultMarkerSize()
        val bitmapDescriptor = getBitmapDescriptor(R.drawable.center_marker, markerSize, markerSize * 2)
        return mMap.addMarker(
            MarkerOptions().position(LatLng(location.latitude, location.longitude))
                .icon(bitmapDescriptor).anchor(0.5f, 0.75f)
        )
    }

    // compute default marker size for the map
    private fun defaultMarkerSize(): Int {
        val displayMetrics = resources.displayMetrics
        return min(displayMetrics.widthPixels, displayMetrics.heightPixels) / 10
    }

    // load vector graphics into a drawable of specified size
    private fun getBitmapDescriptor(id: Int, width: Int, height: Int): BitmapDescriptor? {
        val vectorDrawable = ContextCompat.getDrawable(this, id) ?: return null
        val bm = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888)
        val canvas = Canvas(bm)
        vectorDrawable.setBounds(0, 0, width, height)
        vectorDrawable.draw(canvas)
        return BitmapDescriptorFactory.fromBitmap(bm)
    }

    // called when "Report" button is clicked
    fun onReport(view: View) {
        val url = POST_URL
        val json = JSONObject()
        json.put("latitude",  mLocation?.latitude)
        json.put("longitude", mLocation?.longitude)
        json.put("bearing",   mBearing)

        val request = JsonObjectRequest(Request.Method.POST, url, json, null) { error ->
            error.printStackTrace()
        }
        mRequestQueue.add(request)
    }

    // schedule a periodic update
    private fun scheduleUpdate() {
        val handler = Handler(Looper.getMainLooper())
        handler.removeCallbacks(mUpdateTask)
        handler.postDelayed(mUpdateTask, TARGET_UPDATE_RATE_MS)
    }

    // update list of known targets on the map
    private fun onUpdate() {
        val url = GET_URL
        val request = JsonArrayRequest(Request.Method.GET, url, null, { response ->
            this.updateTargets(getGson().fromJson(response.toString(), Array<Target>::class.java))
            this.scheduleUpdate()
        }, { error ->
            error.printStackTrace()
            this.scheduleUpdate()
        })
        mRequestQueue.add(request)
    }

    private fun updateReportButton() {
        mReportButton.isEnabled = mLocation != null && showLocation
    }
}
