<script setup>
import { ref, onMounted, onUnmounted } from 'vue';

// 创建响应式变量
const message = ref('等待Qt消息...');
const qtInfo = ref(null);
const qtObject = ref(null);
const isConnected = ref(false);

// 初始化WebChannel的函数
const initQWebChannel = () => {
  // 检查Qt对象是否存在
  if (window.qt && window.qt.webChannelTransport) {
    try {
      // 创建QWebChannel实例
      const channel = new QWebChannel(window.qt.webChannelTransport, (channel) => {
        // 获取桥接对象
        qtObject.value = channel.objects.bridge;

        // 连接信号处理函数
        if (qtObject.value) {
          // 处理来自Qt的消息
          qtObject.value.messageFromQt.connect((msg) => {
            message.value = `收到Qt消息: ${msg}`;
            try {
              // 尝试解析JSON数据
              qtInfo.value = JSON.parse(msg);
            } catch (err) {
              console.log('err', err)
            }
          });

          // 发送测试消息到Qt
          setTimeout(() => {
            if (qtObject.value) {
              qtObject.value.processWebMessage('Vue应用已连接');
            }
          }, 1000);

          isConnected.value = true;
          console.log('QWebChannel连接成功');
        } else {
          console.error('未找到桥接对象');
        }
      });
    } catch (error) {
      console.error('QWebChannel初始化错误:', error);
    }
  } else {
    console.warn('Qt对象或webChannelTransport不可用');
  }
};

// 向Qt发送消息的函数
const sendMessageToQt = () => {
  if (qtObject.value) {
    const msg = {
      type: 'fromVue',
      content: '这是来自Vue的消息',
      timestamp: new Date().toISOString()
    };
    qtObject.value.processWebMessage(JSON.stringify(msg));
    message.value = '已发送消息到Qt';
  } else {
    message.value = 'Qt连接未初始化';
  }
};

// 获取Qt版本信息
const getQtVersion = async () => {
  if (qtObject.value && qtObject.value.getQtVersion) {
    try {
      // 异步调用并等待Promise解析
      const version = await qtObject.value.getQtVersion();
      message.value = `Qt版本: ${version}`;
    } catch (error) {
      message.value = '获取Qt版本信息失败';
      return '获取失败';
    }
  } else {
    message.value = '无法获取Qt版本信息';
  }
};

// 处理Web端计算功能
const webCalculator = {
  performCalculation: async (a, b) => {
    if (isConnected.value && qtObject.value) {
      try {
        // 异步调用Qt方法
        const result = await qtObject.value.calculateSum(a, b);
        console.log('计算结果:', result);
        return result;
      } catch (error) {
        console.error('计算失败', error);
        return null;
      }
    } else {
      console.error('无法执行计算: 连接未建立');
      return null;
    }
  }
};

// 页面加载完成后初始化WebChannel
onMounted(() => {
  // 延迟初始化，确保DOM完全加载
  setTimeout(() => {
    console.log('尝试初始化QWebChannel...');
    initQWebChannel();

    // 设置重试机制
    const maxAttempts = 5;
    let attempts = 0;

    const checkConnection = setInterval(() => {
      if (isConnected.value || attempts >= maxAttempts) {
        clearInterval(checkConnection);
        if (!isConnected.value) {
          console.error('QWebChannel连接失败，已达到最大尝试次数');
        }
      } else {
        attempts++;
        console.log(`尝试重新连接QWebChannel (${attempts}/${maxAttempts})`);
        initQWebChannel();
      }
    }, 2000);
  }, 500);
});

// 组件卸载时清理资源
onUnmounted(() => {
  if (qtObject.value) {
    try {
      // 断开所有信号连接
      qtObject.value.messageFromQt.disconnect();
    } catch (e) {
      console.warn('断开信号连接时出错:', e);
    }
  }
});
</script>

<template>
  <div class="container">
    <h3>Qt与Vue通信示例</h3>

    <div class="status">
      <p :class="{ 'connected': isConnected, 'disconnected': !isConnected }">
        {{ isConnected ? '已连接到Qt' : '未连接到Qt' }}
      </p>
    </div>

    <div class="message">
      <p>{{ message }}</p>
      <pre v-if="qtInfo">{{ JSON.stringify(qtInfo, null, 2) }}</pre>
    </div>

    <div class="controls">
      <button @click="sendMessageToQt" :disabled="!isConnected">
        发送消息到Qt
      </button>
      <button @click="getQtVersion" :disabled="!isConnected">
        获取Qt版本
      </button>
    </div>
  </div>
</template>

<style scoped>
.container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  font-family: Arial, sans-serif;
}

.status {
  margin-bottom: 20px;
  padding: 10px;
  border-radius: 4px;
}

.connected {
  background-color: #d4edda;
  color: #155724;
}

.disconnected {
  background-color: #f8d7da;
  color: #721c24;
}

.message {
  margin-bottom: 20px;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  min-height: 100px;
}

pre {
  background-color: #f5f5f5;
  padding: 10px;
  border-radius: 4px;
  overflow-x: auto;
}

.controls {
  display: flex;
  gap: 10px;
}

button {
  padding: 8px 16px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

button:hover {
  background-color: #0056b3;
}

button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}
</style>