from __future__ import absolute_import, division, print_function, unicode_literals
import tensorflow as tf
from tensorflow import keras
import numpy as np
import matplotlib.pyplot as plt
from network import VGG
for gpu in tf.config.experimental.list_physical_devices('GPU'):
    tf.config.experimental.set_memory_growth(gpu, True)

# def load_data(path,files):
#     import gzip
#     import numpy as np
#     paths = [path+ each for each in files ]
#     with gzip.open(paths[0], 'rb') as lbpath:
#         train_labels = np.frombuffer(lbpath.read(), np.uint8, offset=8)
#     with gzip.open(paths[1], 'rb') as impath:
#         train_images = np.frombuffer(impath.read(), np.uint8, offset=16).reshape(len(train_labels),28,28)
#     with gzip.open(paths[2], 'rb') as lbpath:
#         test_labels = np.frombuffer(lbpath.read(), np.uint8, offset=8)
#     with gzip.open(paths[3], 'rb') as impath:
#         test_images = np.frombuffer(impath.read(), np.uint8, offset=16).reshape(len(test_labels), 28, 28)
#     return (train_labels,train_images), (test_labels,test_images)
#
#
#
# path = 'F:/work/pycharm/DeepLearningTutorial-master/ImageClassification/dataset/FASHION-MNIST/'
# files = ['train-labels-idx1-ubyte.gz','train-images-idx3-ubyte.gz', 't10k-labels-idx1-ubyte.gz',  't10k-images-idx3-ubyte.gz']
def load_data(path):
    with np.load(path) as f:
        x_train, y_train = f['x_train'], f['y_train']
        x_test, y_test = f['x_test'], f['y_test']
        return (x_train, y_train), (x_test, y_test)


class DataLoader():
    def __init__(self):
        # initial_data = tf.keras.datasets.fashion_mnist
        # (self.train_images, self.train_labels), (self.test_images, self.test_labels) = load_data(path, files)
        (self.train_images, self.train_labels), (self.test_images, self.test_labels) = load_data(path="./mnist.npz")
        # 将图片转为float32且除255进行归一化；expand_dims增加维度
        self.train_images = np.expand_dims(self.train_images.astype(np.float32)/255.0,axis=-1)
        self.test_images = np.expand_dims(self.test_images.astype(np.float32)/255.0,axis=-1)
        self.train_labels = self.train_labels.astype(np.int32)
        self.test_labels = self.test_labels.astype(np.int32)
        self.num_train, self.num_test = self.train_images.shape[0], self.test_images.shape[0]

    def get_batch_train(self, batch_size):
        # np.random.randint均匀分布，从训练集中随机产生batch_size个索引
        index = np.random.randint(0, np.shape(self.train_images)[0], batch_size)
        # 将图片resize至合适大小,这里原图28×28×1，resize成32×32后训练，若resize成224×224则训练速度较慢
        resized_images = tf.image.resize_with_pad(self.train_images[index],32,32,)
        return resized_images.numpy(), self.train_labels[index]

    def get_batch_test(self, batch_size):
        index = np.random.randint(0, np.shape(self.test_images)[0], batch_size)
        resized_images = tf.image.resize_with_pad(self.test_images[index],32,32,)
        return resized_images.numpy(), self.test_labels[index]


def show_loss_plot(loss_results, accuracy_results):
    fig, axes = plt.subplots(2, sharex=True, figsize=(12, 8))
    fig.suptitle('Training Metrics')
    axes[0].set_ylabel("Loss", fontsize=14)
    axes[0].plot(loss_results)
    axes[1].set_ylabel("Accuracy", fontsize=14)
    axes[1].set_xlabel("Epoch", fontsize=14)
    axes[1].plot(accuracy_results)
    plt.show()


def train_vgg(batch_size, epoch):
    dataLoader = DataLoader()
    # 记录损失和准确率，用于画图
    train_loss_results = []
    train_accuracy_results = []
    # 构建VGG网络 vgg11;vgg16;vgg19
    model = VGG.build_vgg('vgg11')
    # 设置优化器
    optimizer = tf.keras.optimizers.SGD(learning_rate=0.01, momentum=0.8)
    # 设置损失函数
    loss_object = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=False)
    train_loss = tf.keras.metrics.Mean(name='train_loss')
    train_accuracy = tf.keras.metrics.SparseCategoricalAccuracy(name='train_accuracy')
    # 开始训练
    print(1)
    for e in range(epoch):
        num_iter  = dataLoader.num_train//batch_size # 计算1轮epoch需要迭代的批次数
        # Reset the metrics at the start of the next epoch
        train_loss.reset_states()
        train_accuracy.reset_states()
        for i in range(num_iter):
            images, labels = dataLoader.get_batch_train(batch_size)
            with tf.GradientTape() as tape: 
                preds = model(images, training=True)  # 获取预测值
                loss = loss_object(labels, preds)     # 计算损失
                # loss += sum(model.losses)           # 总损失
            gradients = tape.gradient(loss, model.trainable_variables)           # 更新参数梯度
            optimizer.apply_gradients(zip(gradients, model.trainable_variables)) # 更新优化器参数
            train_loss(loss)                          # 更新损失
            train_accuracy(labels, preds)             # 更新准确率
            if i % 20 ==0:
                print('loss',train_loss.result(),'acc',train_accuracy.result())
        train_loss_results.append(train_loss.result())
        train_accuracy_results.append(train_accuracy.result())
        model.save_weights(str (e+1) + "_epoch_vgg11_weight.h5")
        print('Epoch {}, Loss: {}, Accuracy: {}%'.format(e+1,train_loss.result(),train_accuracy.result()*100))
    show_loss_plot(train_loss_results, train_accuracy_results)

    # 用model.fit()训练
    # model.compile(optimizer=optimizer, loss='sparse_categorical_crossentropy', metrics=['accuracy'])
    # for e in range(epoch):
    #     num_iter  = dataLoader.num_train//batch_size
    #     for i in range(num_iter):
    #         images, labels = dataLoader.get_batch_train(batch_size)            
    #         model.fit(images, labels, batch_size=batch_size)
    #     model.save_weights(str (e+1) + "_epoch_vgg11_weight.h5")


def test_vgg(model_path, batch_size):
    dataLoader = DataLoader()
    # 构建VGG网络 vgg11;vgg16;vgg19
    model = VGG.build_vgg('vgg11')
    model.compile(loss='sparse_categorical_crossentropy', metrics=['accuracy'])
    model.build((1,32,32,1))
    model.load_weights(model_path)
    # 显示模型网络结构
    print(model.summary())
    # 评估模型
    test_images, test_labels = dataLoader.get_batch_test(batch_size)
    model.evaluate(test_images, test_labels, verbose=2)


if __name__ == '__main__':
    # 训练
    train_vgg(16, 6) # batch_size recommend 16 for 224×224
    # 测试
    #test_vgg('./weight/20_epoch_vgg11_weight.h5', 10000) # lr 0.01 acc 91.27%
    # test_vgg('./weight/20_epoch_vgg16_weight.h5', 10000) # lr 0.01 acc 92.27%
