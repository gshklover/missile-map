package com.missilemap.missilemap

import org.junit.Test
import org.junit.Assert.*
import com.google.gson.Gson

/**
 * Example local unit test, which will execute on the development machine (host).
 *
 * See [testing documentation](http://d.android.com/tools/testing).
 */
class MissileMapUnitTest {
    @Test
    fun testJsonDecode() {
        val text = "{'start_time': 35, 'speed': 222.40793283838096, 'path': [{'latitude': 45.3742650069553, 'longitude': 33.907561182717544}, {'latitude': 48.46613928701746, 'longitude': 33.28694953006249}]}"
        val target2 = getGson().fromJson<Target>(text, Target::class.java)
        assertEquals(target2.path.size, 2)
    }
}
