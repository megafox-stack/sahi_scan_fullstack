package com.example.app

import android.Manifest
import android.app.Activity
import android.content.Intent
import android.graphics.BitmapFactory
import android.net.Uri
import android.provider.MediaStore
import android.util.Base64
import androidx.activity.result.ActivityResult
import androidx.core.content.FileProvider
import com.getcapacitor.JSObject
import com.getcapacitor.Plugin
import com.getcapacitor.PluginCall
import com.getcapacitor.PluginMethod
import com.getcapacitor.annotation.ActivityCallback
import com.getcapacitor.annotation.CapacitorPlugin
import com.getcapacitor.annotation.Permission
import com.getcapacitor.annotation.PermissionCallback
import java.io.File

@CapacitorPlugin(
    name = "OcrPlugin",
    permissions = [
        Permission(
            alias = "camera",
            strings = [Manifest.permission.CAMERA]
        )
    ]
)
class OcrPlugin : Plugin() {

    private val ocrService by lazy {
        TesseractOcrService(context)
    }

    private var tempPhotoUri: Uri? = null

    @PluginMethod
    fun takePhoto(call: PluginCall) {
        if (!hasRequiredPermissions()) {
            requestPermissionForAlias("camera", call, "cameraPermsCallback")
            return
        }
        openNativeCamera(call)
    }

    @PermissionCallback
    private fun cameraPermsCallback(call: PluginCall) {
        if (hasRequiredPermissions()) {
            openNativeCamera(call)
        } else {
            call.reject("Camera permission is required to capture food label photos.")
        }
    }

    private fun openNativeCamera(call: PluginCall) {
        try {
            val photoFile = File.createTempFile("FOOD_LABEL_", ".jpg", context.cacheDir)
            val uri = FileProvider.getUriForFile(
                context,
                "${context.packageName}.fileprovider",
                photoFile
            )
            tempPhotoUri = uri

            val intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
            intent.putExtra(MediaStore.EXTRA_OUTPUT, uri)
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_GRANT_WRITE_URI_PERMISSION)

            startActivityForResult(call, intent, "cameraResultCallback")
        } catch (e: Exception) {
            call.reject("Could not launch camera: ${e.localizedMessage}")
        }
    }

    @ActivityCallback
    private fun cameraResultCallback(call: PluginCall, result: ActivityResult) {
        val uri = tempPhotoUri
        if (result.resultCode == Activity.RESULT_OK && uri != null) {
            try {
                val bitmap = context.contentResolver.openInputStream(uri)?.use { stream ->
                    BitmapFactory.decodeStream(stream)
                }

                if (bitmap == null) {
                    call.reject("Could not decode captured image bitmap.")
                    return
                }

                val ocrResult = ocrService.processBitmap(bitmap)
                val ret = JSObject()
                ret.put("state", ocrResult.state.name)
                ret.put("text", ocrResult.text)
                ret.put("message", ocrResult.message)
                call.resolve(ret)

            } catch (e: Exception) {
                call.reject("Error processing captured photo: ${e.localizedMessage}")
            }
        } else {
            call.reject("Camera capture was cancelled or failed.")
        }
    }

    @PluginMethod
    fun processImageUri(call: PluginCall) {
        val uriString = call.getString("uri")
        val base64Data = call.getString("base64")

        try {
            val bitmap = when {
                !uriString.isNullOrBlank() -> {
                    val uri = Uri.parse(uriString)
                    context.contentResolver.openInputStream(uri)?.use { stream ->
                        BitmapFactory.decodeStream(stream)
                    }
                }
                !base64Data.isNullOrBlank() -> {
                    val cleanBase64 = if (base64Data.contains(",")) {
                        base64Data.substringAfter(",")
                    } else {
                        base64Data
                    }
                    val decodedBytes = Base64.decode(cleanBase64, Base64.DEFAULT)
                    BitmapFactory.decodeByteArray(decodedBytes, 0, decodedBytes.size)
                }
                else -> null
            }

            if (bitmap == null) {
                call.reject("Could not load bitmap from provided image data.")
                return
            }

            val result = ocrService.processBitmap(bitmap)
            val ret = JSObject()
            ret.put("state", result.state.name)
            ret.put("text", result.text)
            ret.put("message", result.message)
            call.resolve(ret)

        } catch (e: Exception) {
            val ret = JSObject()
            ret.put("state", "OCR_ERROR")
            ret.put("text", "")
            ret.put("message", "Tesseract OCR error: ${e.localizedMessage}")
            call.resolve(ret)
        }
    }
}
