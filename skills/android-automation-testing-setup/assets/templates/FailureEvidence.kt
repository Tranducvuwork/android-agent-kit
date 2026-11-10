// Test-only template: replace this package with the project's test support package.
package replace.with.test.support

import android.graphics.Bitmap
import android.os.Build
import android.util.Log
import androidx.test.platform.app.InstrumentationRegistry
import org.json.JSONObject
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.TimeZone

/** Call INSIDE ActivityScenario.use, around actions/assertions, before UI cleanup. */
object FailureEvidence {
    fun <T> checkpoint(
        runId: String,
        caseId: String,
        attemptId: String,
        checkpointId: String,
        action: () -> T,
    ): T {
        try {
            return action()
        } catch (original: Throwable) {
            try {
                capture(runId, caseId, attemptId, checkpointId)
            } catch (captureError: Throwable) {
                original.addSuppressed(captureError)
                Log.e("FailureEvidence", "Screenshot unavailable for $caseId/$checkpointId", captureError)
            }
            throw original
        }
    }

    private fun capture(runId: String, caseId: String, attemptId: String, checkpointId: String) {
        listOf(runId, caseId, attemptId, checkpointId).forEach {
            require(it.matches(Regex("[A-Za-z0-9_-]+"))) { "Evidence identifiers must be path-safe" }
        }
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        val root = requireNotNull(instrumentation.targetContext.getExternalFilesDir(null))
        val directory = File(root, "automation-evidence/$runId/$caseId/$attemptId")
        check(directory.isDirectory || directory.mkdirs()) { "Cannot create evidence directory" }
        val png = File(directory, "$checkpointId.png")
        check(!png.exists()) { "Use a unique attempt/checkpoint; existing evidence is immutable" }
        val capturedAt = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'", Locale.US)
            .apply { timeZone = TimeZone.getTimeZone("UTC") }.format(Date())
        val bitmap = requireNotNull(instrumentation.uiAutomation.takeScreenshot())
        try {
            png.outputStream().use { check(bitmap.compress(Bitmap.CompressFormat.PNG, 100, it)) }
        } finally {
            bitmap.recycle()
        }
        val metadata = JSONObject()
            .put("run_id", runId).put("case_id", caseId).put("attempt_id", attemptId)
            .put("checkpoint_id", checkpointId).put("captured_at", capturedAt)
            .put("timing", "failure").put("device", Build.MODEL).put("sdk", Build.VERSION.SDK_INT)
        File(directory, "$checkpointId.json").writeText(metadata.toString(2))
        Log.i("FailureEvidence", "Saved ${png.absolutePath}")
    }
}
