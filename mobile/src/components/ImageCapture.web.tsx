/**
 * Web-compatible Image Capture Component
 *
 * Provides image capture functionality for web browsers using the MediaDevices API
 * and standard HTML file input. This is an alternative to the native ImageCapture
 * component which uses expo-camera.
 *
 * Features:
 * - Browser camera access via getUserMedia API
 * - File picker fallback for browsers without camera support
 * - Responsive video preview with capture guide frame
 * - Graceful degradation to file-only mode
 *
 * @module components/ImageCapture.web
 * @author Uday Tamma
 * @license MIT
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
} from 'react-native';

/**
 * Props for the ImageCapture component
 */
interface ImageCaptureProps {
  /** Callback fired when an image is successfully captured or selected */
  onImageCaptured: (uri: string) => void;
  /** Callback fired when user cancels the capture */
  onCancel: () => void;
}

/**
 * Web-compatible image capture component using browser APIs.
 *
 * Attempts to access the device camera via MediaDevices API. If camera access
 * fails or is denied, falls back to a file picker interface.
 *
 * @param props - Component props
 * @returns React component for web image capture
 *
 * @example
 * ```tsx
 * <ImageCapture
 *   onImageCaptured={(uri) => processImage(uri)}
 *   onCancel={() => setShowCamera(false)}
 * />
 * ```
 */
export function ImageCapture({ onImageCaptured, onCancel }: ImageCaptureProps) {
  // Camera stream state
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [hasCamera, setHasCamera] = useState<boolean | null>(null);
  const [isCapturing, setIsCapturing] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);

  // Refs for video and canvas elements
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  /**
   * Initializes camera stream on component mount.
   * Requests camera permission and sets up video preview.
   */
  useEffect(() => {
    let mounted = true;
    let currentStream: MediaStream | null = null;

    const initCamera = async () => {
      try {
        // Check if MediaDevices API is available
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
          throw new Error('Camera API not supported in this browser');
        }

        // Request camera access with rear camera preference
        const mediaStream = await navigator.mediaDevices.getUserMedia({
          video: {
            facingMode: { ideal: 'environment' }, // Prefer rear camera
            width: { ideal: 1920 },
            height: { ideal: 1080 },
          },
        });

        if (mounted) {
          currentStream = mediaStream;
          setStream(mediaStream);
          setHasCamera(true);

          // Attach stream to video element
          if (videoRef.current) {
            videoRef.current.srcObject = mediaStream;
          }
        } else {
          // Component unmounted before stream initialized - clean up
          mediaStream.getTracks().forEach((track) => track.stop());
        }
      } catch (error: any) {
        console.warn('Camera access failed:', error);
        if (mounted) {
          setHasCamera(false);
          setCameraError(
            error.name === 'NotAllowedError'
              ? 'Camera permission denied. Please allow camera access or use file upload.'
              : 'Camera not available. Please use file upload instead.'
          );
        }
      }
    };

    initCamera();

    // Cleanup: stop all tracks when component unmounts
    return () => {
      mounted = false;
      if (currentStream) {
        currentStream.getTracks().forEach((track) => track.stop());
      }
    };
  }, []);

  /**
   * Captures a frame from the video stream and converts to data URL.
   */
  const captureImage = useCallback(async () => {
    if (!videoRef.current || !canvasRef.current || isCapturing) return;

    setIsCapturing(true);
    try {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      const context = canvas.getContext('2d');

      if (!context) throw new Error('Canvas context not available');

      // Set canvas size to match video dimensions
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;

      // Draw current video frame to canvas
      context.drawImage(video, 0, 0, canvas.width, canvas.height);

      // Convert to data URL (JPEG at 80% quality for balance of size/quality)
      const dataUrl = canvas.toDataURL('image/jpeg', 0.8);
      onImageCaptured(dataUrl);
    } catch (error) {
      console.error('Failed to capture image:', error);
      alert('Failed to capture image. Please try again or use file upload.');
    } finally {
      setIsCapturing(false);
    }
  }, [isCapturing, onImageCaptured]);

  /**
   * Handles file selection from the file input.
   */
  const handleFileSelect = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      if (!file) return;

      // Validate file type
      if (!file.type.startsWith('image/')) {
        alert('Please select an image file');
        return;
      }

      // Convert file to data URL
      const reader = new FileReader();
      reader.onload = (e) => {
        const dataUrl = e.target?.result as string;
        if (dataUrl) {
          onImageCaptured(dataUrl);
        }
      };
      reader.onerror = () => {
        alert('Failed to read image file. Please try again.');
      };
      reader.readAsDataURL(file);
    },
    [onImageCaptured]
  );

  /**
   * Opens the file picker dialog.
   */
  const openFilePicker = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  /**
   * Handles component cancellation and cleans up camera stream.
   */
  const handleCancel = useCallback(() => {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
    }
    onCancel();
  }, [stream, onCancel]);

  // Loading state while checking camera availability
  if (hasCamera === null) {
    return (
      <View style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#6366f1" />
          <Text style={styles.loadingText}>Initializing camera...</Text>
        </View>
      </View>
    );
  }

  // File-only mode when camera is not available
  if (!hasCamera) {
    return (
      <View style={styles.container}>
        <View style={styles.fallbackContainer}>
          <Text style={styles.fallbackTitle}>Upload Image</Text>
          <Text style={styles.fallbackText}>
            {cameraError || 'Select an image of the ingredient label'}
          </Text>

          <TouchableOpacity style={styles.uploadButton} onPress={openFilePicker}>
            <Text style={styles.uploadButtonIcon}>📁</Text>
            <Text style={styles.uploadButtonText}>Choose Image</Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.cancelButton} onPress={handleCancel}>
            <Text style={styles.cancelButtonText}>Cancel</Text>
          </TouchableOpacity>

          {/* Hidden file input */}
          <input
            ref={fileInputRef as any}
            type="file"
            accept="image/*"
            onChange={handleFileSelect as any}
            style={{ display: 'none' }}
          />
        </View>
      </View>
    );
  }

  // Camera mode
  return (
    <View style={styles.container}>
      {/* Video preview */}
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        style={webStyles.video}
      />

      {/* Hidden canvas for image capture */}
      <canvas ref={canvasRef} style={{ display: 'none' }} />

      {/* Hidden file input for gallery option */}
      <input
        ref={fileInputRef as any}
        type="file"
        accept="image/*"
        onChange={handleFileSelect as any}
        style={{ display: 'none' }}
      />

      {/* Overlay with controls */}
      <View style={styles.overlayContainer}>
        {/* Guide frame */}
        <View style={styles.overlay}>
          <View style={styles.guideFrame}>
            <Text style={styles.guideText}>
              Position ingredient label within frame
            </Text>
          </View>
        </View>

        {/* Controls */}
        <View style={styles.controls}>
          <TouchableOpacity style={styles.controlButton} onPress={openFilePicker}>
            <Text style={styles.controlIcon}>📁</Text>
            <Text style={styles.controlLabel}>Gallery</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.captureButton, isCapturing && styles.capturing]}
            onPress={captureImage}
            disabled={isCapturing}
          >
            {isCapturing ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <View style={styles.captureInner} />
            )}
          </TouchableOpacity>

          <View style={styles.controlButton}>
            {/* Placeholder for symmetry - web doesn't need flip */}
            <Text style={styles.controlIcon}>📷</Text>
            <Text style={styles.controlLabel}>Camera</Text>
          </View>
        </View>

        {/* Cancel button */}
        <TouchableOpacity style={styles.cancelButtonOverlay} onPress={handleCancel}>
          <Text style={styles.cancelText}>✕</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

/**
 * Web-specific styles using standard CSS properties
 */
const webStyles: { [key: string]: React.CSSProperties } = {
  video: {
    width: '100%',
    height: '100%',
    objectFit: 'cover' as const,
  },
};

/**
 * React Native StyleSheet for cross-platform styling
 */
const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#1a1a1a',
  },
  loadingText: {
    color: '#fff',
    fontSize: 16,
    marginTop: 16,
  },
  fallbackContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#1a1a1a',
    padding: 24,
  },
  fallbackTitle: {
    color: '#fff',
    fontSize: 24,
    fontWeight: '700',
    marginBottom: 12,
  },
  fallbackText: {
    color: '#9ca3af',
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 32,
    maxWidth: 300,
  },
  uploadButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#6366f1',
    paddingHorizontal: 32,
    paddingVertical: 16,
    borderRadius: 12,
    gap: 12,
  },
  uploadButtonIcon: {
    fontSize: 20,
  },
  uploadButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
  cancelButton: {
    marginTop: 20,
    paddingVertical: 12,
    paddingHorizontal: 24,
  },
  cancelButtonText: {
    color: '#9ca3af',
    fontSize: 16,
  },
  overlayContainer: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    justifyContent: 'space-between',
  },
  overlay: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  guideFrame: {
    width: '85%',
    height: 200,
    borderWidth: 2,
    borderColor: '#fff',
    borderRadius: 8,
    justifyContent: 'flex-end',
    alignItems: 'center',
    paddingBottom: 10,
  },
  guideText: {
    color: '#fff',
    fontSize: 14,
    textAlign: 'center',
    backgroundColor: 'rgba(0,0,0,0.5)',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 4,
  },
  controls: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
    paddingVertical: 30,
    paddingHorizontal: 20,
    backgroundColor: 'rgba(0,0,0,0.5)',
  },
  controlButton: {
    alignItems: 'center',
    padding: 10,
  },
  controlIcon: {
    fontSize: 24,
  },
  controlLabel: {
    color: '#fff',
    fontSize: 12,
    marginTop: 4,
  },
  captureButton: {
    width: 70,
    height: 70,
    borderRadius: 35,
    backgroundColor: '#fff',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 4,
    borderColor: '#ccc',
  },
  capturing: {
    opacity: 0.6,
  },
  captureInner: {
    width: 54,
    height: 54,
    borderRadius: 27,
    backgroundColor: '#fff',
  },
  cancelButtonOverlay: {
    position: 'absolute',
    top: 50,
    right: 20,
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  cancelText: {
    color: '#fff',
    fontSize: 20,
    fontWeight: 'bold',
  },
});
