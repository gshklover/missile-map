package com.example.missilemap

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.location.Location
import android.location.LocationListener
import android.location.LocationManager
import android.os.Bundle
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import com.google.android.gms.maps.*
import com.google.android.gms.maps.model.CameraPosition
import com.google.android.gms.maps.model.LatLng
import kotlin.math.roundToInt

val DEFAULT_ZOOM : Float = 10.0f  // default map zoom
val UPDATE_RATE_MS : Long = 100    // minimum time (ms) between map updates

/**
 * Main application activity
 */
class MainActivity : AppCompatActivity(), LocationListener, SensorEventListener, OnMapReadyCallback {

    // visual elements:
    private lateinit var mTextView: TextView        // text field that displays the location
    // private lateinit var mArrow: View
    private lateinit var mMap: GoogleMap
    private var mLastUpdateTime: Long = 0         // last update time mMap

    // sensor readings:
    private val mGravity = FloatArray(3) { _ -> 0.0f }      // current accelerometer reading
    private val mGeomagnetic = FloatArray(3) { _ -> 0.0f }  // current magnetic sensor reading
    private var mLocation : Location? = null                     // current location
    private var mBearing : Float = 0f                            // current phone bearing (radians, [-pi..+pi])

    // called when the activity is first created
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        mTextView = findViewById<TextView>(R.id.textView)
        // mArrow = findViewById<View>(R.id.canvas)

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
    }

    // called when main activity is paused (no in foreground)
    override fun onPause() {
        super.onPause()

        val sensorManager = getSystemService(Context.SENSOR_SERVICE) as SensorManager
        sensorManager.unregisterListener(this)

        val locationManager = getSystemService(Context.LOCATION_SERVICE) as LocationManager
        locationManager.removeUpdates(this)
    }

    // called by LocationManager when location changes
    override fun onLocationChanged(location: Location) {
        mLocation = location
        updateText()
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
            val locationManager = getSystemService(Context.LOCATION_SERVICE) as LocationManager
            locationManager.requestLocationUpdates(LocationManager.GPS_PROVIDER, 0, 0.1f, this)
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
            // FIXME: when rotating around south, this method DOES NOT WORK WELL
            //        need to find shortest angle distance between previous and new bearing (not necessary through north)
            mBearing = alpha * mBearing  + (1 - alpha) * orientation[0]
            updateText()
        }
    }

    // not used
    override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {}

    // update displayed text
    private fun updateText() {
        val longitude = mLocation?.longitude
        val latitude = mLocation?.latitude
        val bearing = Math.toDegrees(mBearing.toDouble()).roundToInt()
        mTextView.setText(
            """
                Location: ${latitude.toString()} : ${longitude.toString()}
                Bearing: ${bearing}
            """.trimIndent()
        )

        // mArrow.rotation = azimuth.toFloat()
        if (::mMap.isInitialized && latitude != null && longitude != null) {
            val currentTime = System.currentTimeMillis()
            if (currentTime < mLastUpdateTime || currentTime > mLastUpdateTime + UPDATE_RATE_MS) {
                mLastUpdateTime = currentTime
                val currentPos = mMap.cameraPosition
                val newPos = CameraPosition(
                    LatLng(latitude, longitude),
                    currentPos.zoom,
                    0f,
                    Math.toDegrees(mBearing.toDouble()).toFloat()
                )
                mMap.moveCamera(CameraUpdateFactory.newCameraPosition(newPos))
            }
        }
    }

    // implements OnMapReadyCallback interface
    override fun onMapReady(googleMap: GoogleMap) {
        mMap = googleMap
        // mMap.isMyLocationEnabled = true - for automatic tracking by google maps

        var location = mLocation
        if (location == null) {
            location = Location(LocationManager.GPS_PROVIDER)
            location.latitude = 34.0
            location.longitude = 47.0
        }
        mMap.moveCamera(CameraUpdateFactory.newLatLngZoom(LatLng(location.latitude, location.longitude), DEFAULT_ZOOM));
//        mMap.addMarker(MarkerOptions().position(sydney).title("Marker in Sydney"))
    }
}
