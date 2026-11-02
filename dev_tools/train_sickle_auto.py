# train_sickle_auto.py
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import matplotlib.pyplot as plt
import os
import numpy as np
from sklearn.model_selection import train_test_split
import shutil
import zipfile
import subprocess

print("="*60)
print("SICKLE CELL MODEL TRAINING")
print("="*60)

# ============================================
# STEP 1: DOWNLOAD DATASET FROM KAGGLE
# ============================================
print("\n[STEP 1] Downloading dataset from Kaggle...")

# Check if kaggle is installed
try:
    subprocess.run(['kaggle', '--version'], capture_output=True, check=True)
    print("[OK] Kaggle CLI found")
    
    # Download dataset
    os.makedirs('sickle_cell_dataset', exist_ok=True)
    result = subprocess.run(
        ['kaggle', 'datasets', 'download', '-d', 'florencetushabe/sickle-cell-disease-dataset', 
         '-p', 'sickle_cell_dataset', '--force'],
        capture_output=True
    )
    
    if result.returncode == 0:
        print("[OK] Dataset downloaded!")
        
        # Extract
        zip_path = 'sickle_cell_dataset/sickle-cell-disease-dataset.zip'
        if os.path.exists(zip_path):
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall('sickle_cell_dataset')
            print("[OK] Dataset extracted!")
    else:
        print("[WARNING] Kaggle download failed, trying manual download...")
        raise Exception("Kaggle download failed")
        
except Exception as e:
    print(f"[WARNING] Kaggle error: {e}")
    print("\n[MANUAL DOWNLOAD REQUIRED]")
    print("   1. Go to: https://www.kaggle.com/datasets/florencetushabe/sickle-cell-disease-dataset")
    print("   2. Click 'Download'")
    print("   3. Extract the zip to: D:\\BloodConnect\\backend\\sickle_cell_dataset\\")
    input("\nPress Enter after you've placed the dataset...")

# ============================================
# STEP 2: PREPARE DATASET
# ============================================
print("\n[STEP 2] Preparing dataset...")

DATASET_PATH = r'D:\BloodConnect\backend\sickle_cell_dataset'

if not os.path.exists(DATASET_PATH):
    print(f"[ERROR] Dataset not found at {DATASET_PATH}")
    exit(1)

# Find images
sickle_images = []
normal_images = []

print("\nScanning for images...")
for root, dirs, files in os.walk(DATASET_PATH):
    for file in files:
        if file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
            file_path = os.path.join(root, file)
            if 'positive' in root.lower() or 'sickle' in root.lower():
                sickle_images.append(file_path)
            elif 'clear' in root.lower() or 'negative' in root.lower() or 'normal' in root.lower():
                normal_images.append(file_path)

print(f"Sickle cell images: {len(sickle_images)}")
print(f"Normal images: {len(normal_images)}")

if len(sickle_images) == 0 or len(normal_images) == 0:
    print("\n[ERROR] No images found! Please check dataset structure.")
    print("Expected folders: 'Positive' and 'Clear' or 'Negative'")
    exit(1)

# ============================================
# STEP 3: CREATE TRAIN/VAL SPLITS
# ============================================
print("\n[STEP 3] Creating train/validation splits...")

# Create folders
os.makedirs('sickle_train/sickle', exist_ok=True)
os.makedirs('sickle_train/normal', exist_ok=True)
os.makedirs('sickle_val/sickle', exist_ok=True)
os.makedirs('sickle_val/normal', exist_ok=True)

# Split
train_sickle, val_sickle = train_test_split(sickle_images, test_size=0.2, random_state=42)
train_normal, val_normal = train_test_split(normal_images, test_size=0.2, random_state=42)

print(f"Training: {len(train_sickle)} sickle, {len(train_normal)} normal")
print(f"Validation: {len(val_sickle)} sickle, {len(val_normal)} normal")

# Copy files
print("\nCopying training files...")
for img in train_sickle:
    shutil.copy(img, f'sickle_train/sickle/{os.path.basename(img)}')
for img in train_normal:
    shutil.copy(img, f'sickle_train/normal/{os.path.basename(img)}')
for img in val_sickle:
    shutil.copy(img, f'sickle_val/sickle/{os.path.basename(img)}')
for img in val_normal:
    shutil.copy(img, f'sickle_val/normal/{os.path.basename(img)}')

# ============================================
# STEP 4: TRAIN MODEL
# ============================================
print("\n[STEP 4] Training model...")

IMG_SIZE = 128
BATCH_SIZE = 32
EPOCHS = 20

train_datagen = ImageDataGenerator(
    rescale=1./255,
    rotation_range=20,
    width_shift_range=0.1,
    height_shift_range=0.1,
    horizontal_flip=True,
    zoom_range=0.1
)

val_datagen = ImageDataGenerator(rescale=1./255)

train_generator = train_datagen.flow_from_directory(
    'sickle_train',
    target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    class_mode='binary'
)

val_generator = val_datagen.flow_from_directory(
    'sickle_val',
    target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    class_mode='binary'
)

# Build model
model = tf.keras.Sequential([
    tf.keras.layers.Conv2D(32, 3, activation='relu', input_shape=(IMG_SIZE, IMG_SIZE, 3)),
    tf.keras.layers.MaxPooling2D(),
    tf.keras.layers.Conv2D(64, 3, activation='relu'),
    tf.keras.layers.MaxPooling2D(),
    tf.keras.layers.Conv2D(128, 3, activation='relu'),
    tf.keras.layers.GlobalAveragePooling2D(),
    tf.keras.layers.Dropout(0.5),
    tf.keras.layers.Dense(1, activation='sigmoid')
])

model.compile(
    optimizer='adam',
    loss='binary_crossentropy',
    metrics=['accuracy']
)

model.summary()

# Train
print("\n" + "="*60)
print("STARTING TRAINING")
print("="*60)

history = model.fit(
    train_generator,
    validation_data=val_generator,
    epochs=EPOCHS,
    verbose=1
)

# ============================================
# STEP 5: EVALUATE AND SAVE
# ============================================
print("\n[STEP 5] Evaluating model...")

# Plot results
fig, axes = plt.subplots(1, 2, figsize=(12, 4))

axes[0].plot(history.history['accuracy'], label='Train Accuracy')
axes[0].plot(history.history['val_accuracy'], label='Val Accuracy')
axes[0].set_title('Model Accuracy')
axes[0].set_xlabel('Epoch')
axes[0].set_ylabel('Accuracy')
axes[0].legend()
axes[0].grid(True)

axes[1].plot(history.history['loss'], label='Train Loss')
axes[1].plot(history.history['val_loss'], label='Val Loss')
axes[1].set_title('Model Loss')
axes[1].set_xlabel('Epoch')
axes[1].set_ylabel('Loss')
axes[1].legend()
axes[1].grid(True)

plt.tight_layout()
plt.savefig('sickle_training_results.png')
plt.show()

# Evaluate
val_loss, val_acc = model.evaluate(val_generator, verbose=0)
print(f"\n[OK] Validation Accuracy: {val_acc:.4f} ({val_acc*100:.2f}%)")

# Save model
os.makedirs('models', exist_ok=True)
model.save('models/sickle_cell_model_trained.h5')
print("\n[OK] Model saved as models/sickle_cell_model_trained.h5")

# ============================================
# STEP 6: TEST SAMPLE PREDICTIONS
# ============================================
print("\n[STEP 6] Testing sample predictions...")

test_sickle = val_sickle[:5]
test_normal = val_normal[:5]

print("\nSickle cell samples:")
for img in test_sickle:
    img_data = tf.keras.preprocessing.image.load_img(img, target_size=(IMG_SIZE, IMG_SIZE))
    img_array = tf.keras.preprocessing.image.img_to_array(img_data) / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    pred = model.predict(img_array, verbose=0)[0][0]
    print(f"  {os.path.basename(img)}: {pred:.4f} -> {'SICKLE' if pred > 0.5 else 'NORMAL'}")

print("\nNormal samples:")
for img in test_normal:
    img_data = tf.keras.preprocessing.image.load_img(img, target_size=(IMG_SIZE, IMG_SIZE))
    img_array = tf.keras.preprocessing.image.img_to_array(img_data) / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    pred = model.predict(img_array, verbose=0)[0][0]
    print(f"  {os.path.basename(img)}: {pred:.4f} -> {'SICKLE' if pred > 0.5 else 'NORMAL'}")

print("\n" + "="*60)
print("TRAINING COMPLETE")
print("="*60)
print("\nModel saved at: D:\\BloodConnect\\backend\\models\\sickle_cell_model_trained.h5")
print("\nNext steps:")
print("1. Update disease_detector.py to use 'sickle_cell_model_trained.h5'")
print("2. Restart Flask: python app.py")