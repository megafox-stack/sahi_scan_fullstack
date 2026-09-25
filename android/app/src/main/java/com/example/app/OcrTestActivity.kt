package com.example.app

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.graphics.BitmapFactory
import android.net.Uri
import android.os.Bundle
import android.view.View
import android.widget.Button
import android.widget.ImageView
import android.widget.ProgressBar
import android.widget.TextView
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.FileProvider
import java.io.File

class OcrTestActivity : AppCompatActivity() {

    private lateinit var statusView: TextView
    private lateinit var resultView: TextView
    private lateinit var copyBtn: Button
    private lateinit var captureBtn: Button
    private lateinit var galleryBtn: Button
    private lateinit var scanAgainBtn: Button
    private lateinit var progress: ProgressBar
    private lateinit var previewImage: ImageView

    private var photoUri: Uri? = null

    private val ocrService by lazy {
        TesseractOcrService(this)
    }

    private val pickImageLauncher = registerForActivityResult(ActivityResultContracts.GetContent()) { uri: Uri? ->
        if (uri != null) {
            previewImage.setImageURI(uri)
            previewImage.visibility = View.VISIBLE
            processUriImage(uri)
        } else {
            updateState(TesseractState.READY, "No image was selected from gallery.")
        }
    }

    private val takePhotoLauncher = registerForActivityResult(ActivityResultContracts.TakePicture()) { success ->
        val uri = photoUri
        if (success && uri != null) {
            previewImage.setImageURI(uri)
            previewImage.visibility = View.VISIBLE
            processUriImage(uri)
        } else {
            updateState(TesseractState.READY, "Camera capture cancelled or failed.")
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_ocr_test)

        statusView = findViewById(R.id.ocr_status)
        resultView = findViewById(R.id.ocr_result)
        copyBtn = findViewById(R.id.ocr_copy)
        captureBtn = findViewById(R.id.ocr_capture)
        galleryBtn = findViewById(R.id.ocr_gallery)
        scanAgainBtn = findViewById(R.id.ocr_scan_again)
        progress = findViewById(R.id.ocr_progress)
        previewImage = findViewById(R.id.ocr_image_preview)

        updateState(TesseractState.READY, "Select a food package image or take a photo.")

        galleryBtn.setOnClickListener {
            updateState(TesseractState.PROCESSING_IMAGE, "Opening Android Gallery...")
            pickImageLauncher.launch("image/*")
        }

        captureBtn.setOnClickListener {
            launchCamera()
        }

        scanAgainBtn.setOnClickListener {
            resetScanState()
        }

        copyBtn.setOnClickListener {
            copyTextToClipboard()
        }
    }

    private fun launchCamera() {
        try {
            updateState(TesseractState.PROCESSING_IMAGE, "Preparing camera...")
            val photoFile = File.createTempFile("FOOD_OCR_", ".jpg", cacheDir)
            val uri = FileProvider.getUriForFile(this, "${applicationContext.packageName}.fileprovider", photoFile)
            photoUri = uri
            takePhotoLauncher.launch(uri)
        } catch (e: Exception) {
            updateState(TesseractState.OCR_ERROR, "Failed to launch camera: ${e.localizedMessage}")
        }
    }

    private fun processUriImage(uri: Uri) {
        try {
            updateState(TesseractState.PROCESSING_IMAGE, "Loading selected food bitmap...")
            progress.visibility = View.VISIBLE

            val bitmap = contentResolver.openInputStream(uri)?.use { stream ->
                BitmapFactory.decodeStream(stream)
            }

            if (bitmap == null) {
                progress.visibility = View.GONE
                updateState(TesseractState.OCR_ERROR, "Failed to decode bitmap from selected Uri.")
                resultView.text = "Error: Invalid image format."
                return
            }

            updateState(TesseractState.RUNNING_OCR, "Running Tesseract4Android OCR...")

            Thread {
                val ocrResult = ocrService.processBitmap(bitmap)
                runOnUiThread {
                    progress.visibility = View.GONE
                    updateState(ocrResult.state, ocrResult.message)
                    if (ocrResult.state == TesseractState.OCR_COMPLETE) {
                        resultView.text = ocrResult.text
                    } else if (ocrResult.state == TesseractState.NO_TEXT_DETECTED) {
                        resultView.text = "No text detected."
                    } else {
                        resultView.text = ocrResult.message
                    }
                }
            }.start()

        } catch (e: Exception) {
            progress.visibility = View.GONE
            updateState(TesseractState.OCR_ERROR, "Image processing error: ${e.localizedMessage}")
        }
    }

    private fun updateState(state: TesseractState, detail: String) {
        statusView.text = "STATE: ${state.name}\n$detail"
    }

    private fun resetScanState() {
        updateState(TesseractState.READY, "Ready to scan another food package image.")
        resultView.text = "[No image processed yet]"
        previewImage.visibility = View.GONE
        progress.visibility = View.GONE
    }

    private fun copyTextToClipboard() {
        val txt = resultView.text.toString()
        if (txt.isBlank() || txt.startsWith("[No image") || txt == "No text detected.") {
            updateState(TesseractState.READY, "No valid OCR text available to copy.")
            return
        }
        val clipboard = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
        val clip = ClipData.newPlainText("SahiScan_OCR", txt)
        clipboard.setPrimaryClip(clip)
        updateState(TesseractState.OCR_COMPLETE, "Copied OCR text to clipboard.")
    }
}
