# train_sickle_balanced.py
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from sklearn.model_selection import train_test_split
from sklearn.utils import class_weight
import matplotlib.pyplot as plt
import os
import shutil
import numpy as np
import random

print("="*60)
print("SICKLE CELL MODEL - BALANCED TRAINING")
print("="*60)

# Configuration
IMG_SIZE = 128
BATCH_SIZE = 32
EPOCHS = 30

DATASET_PATH = r"D:\BloodConnect\sickle"

# ============================================
# STEP 1: FIND ALL IMAGES
# ============================================
print("\n[STEP 1] Scanning dataset...")

sickle_images = []
normal_images = []

positive_path = os.path.join(DATASET_PATH, "Positive")
if os.path.exists(positive_path):
    for root, dirs, files in os.walk(positive_path):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                sickle_images.append(os.path.join(root, file))

negative_path = os.path.join(DATASET_PATH, "Negative")
if os.path.exists(negative_path):
    for root, dirs, files in os.walk(negative_path):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                normal_images.append(os.path.join(root, file))

print(f"Sickle cell images: {len(sickle_images)}")
print(f"Normal images: {len(normal_images)}")

# Balance the dataset by using the smaller class size
min_count = min(len(sickle_images), len(normal_images))
print(f"\nBalancing dataset to {min_count} images per class")

# Randomly select equal number of images
random.seed(42)
sickle_images = random.sample(sickle_images, min_count)
normal_images = random.sample(normal_images, min_count)

print(f"After balancing:")
print(f"  Sickle: {len(sickle_images)}")
print(f"  Normal: {len(normal_images)}")

# ============================================
# STEP 2: CREATE TRAIN/VALIDATION SPLITS
# ============================================
print("\n[STEP 2] Creating splits...")

train_sickle, val_sickle = train_test_split(
    sickle_images, test_size=0.2, random_state=42
)
train_normal, val_normal = train_test_split(
    normal_images, test_size=0.2, random_state=42
)

print(f"\nTraining:")
print(f"  Sickle: {len(train_sickle)}")
print(f"  Normal: {len(train_normal)}")
print(f"\nValidation:")
print(f"  Sickle: {len(val_sickle)}")
print(f"  Normal: {len(val_normal)}")

# ============================================
# STEP 3: PREPARE FOLDERS
# ============================================
print("\n[STEP 3] Preparing folders...")

TRAIN_DIR = "sickle_train_balanced"
VAL_DIR = "sickle_val_balanced"

if os.path.exists(TRAIN_DIR):
    shutil.rmtree(TRAIN_DIR)
if os.path.exists(VAL_DIR):
    shutil.rmtree(VAL_DIR)

os.makedirs(f"{TRAIN_DIR}/sickle", exist_ok=True)
os.makedirs(f"{TRAIN_DIR}/normal", exist_ok=True)
os.makedirs(f"{VAL_DIR}/sickle", exist_ok=True)
os.makedirs(f"{VAL_DIR}/normal", exist_ok=True)

print("Copying files...")
for img in train_sickle:
    shutil.copy(img, f"{TRAIN_DIR}/sickle/{os.path.basename(img)}")
for img in train_normal:
    shutil.copy(img, f"{TRAIN_DIR}/normal/{os.path.basename(img)}")
for img in val_sickle:
    shutil.copy(img, f"{VAL_DIR}/sickle/{os.path.basename(img)}")
for img in val_normal:
    shutil.copy(img, f"{VAL_DIR}/normal/{os.path.basename(img)}")

# ============================================
# STEP 4: DATA GENERATORS
# ============================================
print("\n[STEP 4] Setting up generators...")

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
    TRAIN_DIR,
    target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    class_mode='binary'
)

val_generator = val_datagen.flow_from_directory(
    VAL_DIR,
    target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    class_mode='binary'
)

# ============================================
# STEP 5: CALCULATE CLASS WEIGHTS
# ============================================
print("\n[STEP 5] Calculating class weights...")

total = len(train_sickle) + len(train_normal)
weight_for_sickle = total / (2 * len(train_sickle))
weight_for_normal = total / (2 * len(train_normal))

class_weights = {0: weight_for_normal, 1: weight_for_sickle}
print(f"Class weights: {class_weights}")

# ============================================
# STEP 6: BUILD MODEL
# ============================================
print("\n[STEP 6] Building model...")

model = tf.keras.Sequential([
    tf.keras.layers.Input(shape=(IMG_SIZE, IMG_SIZE, 3)),
    tf.keras.layers.Conv2D(32, 3, activation='relu'),
    tf.keras.layers.MaxPooling2D(),
    tf.keras.layers.Conv2D(64, 3, activation='relu'),
    tf.keras.layers.MaxPooling2D(),
    tf.keras.layers.Conv2D(128, 3, activation='relu'),
    tf.keras.layers.GlobalAveragePooling2D(),
    tf.keras.layers.Dropout(0.5),
    tf.keras.layers.Dense(64, activation='relu'),
    tf.keras.layers.Dropout(0.3),
    tf.keras.layers.Dense(1, activation='sigmoid')
])

model.compile(
    optimizer='adam',
    loss='binary_crossentropy',
    metrics=['accuracy', tf.keras.metrics.Precision(), tf.keras.metrics.Recall()]
)

model.summary()

# ============================================
# STEP 7: TRAIN WITH CLASS WEIGHTS
# ============================================
print("\n[STEP 7] Training with balanced class weights...")
print("="*60)

callbacks = [
    tf.keras.callbacks.EarlyStopping(
        monitor='val_loss',
        patience=5,
        restore_best_weights=True,
        verbose=1
    ),
    tf.keras.callbacks.ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.5,
        patience=3,
        verbose=1
    ),
    tf.keras.callbacks.ModelCheckpoint(
        'models/sickle_cell_balanced.h5',
        monitor='val_accuracy',
        save_best_only=True,
        verbose=1
    )
]

history = model.fit(
    train_generator,
    validation_data=val_generator,
    epochs=EPOCHS,
    class_weight=class_weights,
    callbacks=callbacks,
    verbose=1
)

# ============================================
# STEP 8: EVALUATE
# ============================================
print("\n[STEP 8] Evaluating...")

val_loss, val_acc, val_precision, val_recall = model.evaluate(val_generator, verbose=0)
print(f"\nValidation Accuracy: {val_acc:.4f} ({val_acc*100:.2f}%)")
print(f"Validation Precision: {val_precision:.4f}")
print(f"Validation Recall: {val_recall:.4f}")

# ============================================
# STEP 9: SAVE MODEL
# ============================================
print("\n[STEP 9] Saving model...")

os.makedirs('models', exist_ok=True)
model.save('models/sickle_cell_model.h5')
print("Model saved: models/sickle_cell_model.h5")

# ============================================
# STEP 10: TEST SAMPLES
# ============================================
print("\n[STEP 10] Testing samples...")

def predict_image(image_path):
    img = tf.keras.preprocessing.image.load_img(image_path, target_size=(IMG_SIZE, IMG_SIZE))
    img_array = tf.keras.preprocessing.image.img_to_array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    return model.predict(img_array, verbose=0)[0][0]

print("\nSickle cell samples:")
for img in val_sickle[:5]:
    pred = predict_image(img)
    result = "SICKLE" if pred > 0.5 else "NORMAL"
    print(f"  {os.path.basename(img)}: {pred:.4f} -> {result}")

print("\nNormal samples:")
for img in val_normal[:5]:
    pred = predict_image(img)
    result = "SICKLE" if pred > 0.5 else "NORMAL"
    print(f"  {os.path.basename(img)}: {pred:.4f} -> {result}")

print("\n" + "="*60)
print("TRAINING COMPLETE")
print("="*60)