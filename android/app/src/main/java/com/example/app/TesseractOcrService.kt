package com.example.app

import android.content.Context
import android.graphics.Bitmap
import com.googlecode.tesseract.android.TessBaseAPI
import java.io.File
import java.io.FileOutputStream

enum class TesseractState {
    READY,
    PROCESSING_IMAGE,
    RUNNING_OCR,
    OCR_COMPLETE,
    NO_TEXT_DETECTED,
    OCR_ERROR
}

data class TesseractOcrResult(
    val state: TesseractState,
    val text: String,
    val message: String
)

class TesseractOcrService(private val context: Context) {

    private fun ensureTrainedDataExists(): File {
        val tessDir = File(context.filesDir, "tessdata")
        if (!tessDir.exists()) {
            tessDir.mkdirs()
        }

        val trainedDataFile = File(tessDir, "eng.traineddata")
        if (!trainedDataFile.exists() || trainedDataFile.length() == 0L) {
            context.assets.open("tessdata/eng.traineddata").use { input ->
                FileOutputStream(trainedDataFile).use { output ->
                    input.copyTo(output)
                }
            }
        }

        if (!trainedDataFile.exists() || trainedDataFile.length() == 0L) {
            throw IllegalStateException("eng.traineddata file was not found in asset or storage.")
        }

        return trainedDataFile
    }

    fun processBitmap(bitmap: Bitmap): TesseractOcrResult {
        var tessApi: TessBaseAPI? = null
        return try {
            ensureTrainedDataExists()

            tessApi = TessBaseAPI()
            val dataPath = context.filesDir.absolutePath
            val success = tessApi.init(dataPath, "eng")

            if (!success) {
                return TesseractOcrResult(
                    state = TesseractState.OCR_ERROR,
                    text = "",
                    message = "Failed to initialize Tesseract4Android engine."
                )
            }

            tessApi.setImage(bitmap)
            val extractedText = tessApi.utF8Text?.trim() ?: ""

            if (extractedText.isBlank()) {
                TesseractOcrResult(
                    state = TesseractState.NO_TEXT_DETECTED,
                    text = "",
                    message = "No text detected."
                )
            } else {
                TesseractOcrResult(
                    state = TesseractState.OCR_COMPLETE,
                    text = extractedText,
                    message = "Tesseract OCR processing complete."
                )
            }
        } catch (e: Exception) {
            TesseractOcrResult(
                state = TesseractState.OCR_ERROR,
                text = "",
                message = "Tesseract OCR Error: ${e.localizedMessage}"
            )
        } finally {
            try {
                tessApi?.recycle()
            } catch (_: Exception) {}
        }
    }
}
