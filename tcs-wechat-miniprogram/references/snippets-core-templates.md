# 小程序核心代码模板

可直接改用的骨架代码。API 细节以微信官方文档为准，不确定的参数标注「需核实」。

## 1 统一请求层（utils/request.js）

```javascript
const BASE_URL = 'https://api.example.com/miniapp/v1';

const request = (options) => {
  return new Promise((resolve, reject) => {
    const token = wx.getStorageSync('access_token');
    wx.request({
      url: `${BASE_URL}${options.url}`,
      method: options.method || 'GET',
      data: options.data || {},
      header: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : '',
        ...options.header,
      },
      success: (res) => {
        if (res.statusCode === 401) {
          // Token 过期，刷新后重试原请求
          return refreshTokenAndRetry(options).then(resolve).catch(reject);
        }
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data);
        } else {
          reject({ code: res.statusCode, message: res.data.message || 'Request failed' });
        }
      },
      fail: (err) => reject({ code: -1, message: 'Network error', detail: err }),
    });
  });
};

// 微信登录：wx.login 换 code → 服务端换 session/token
const login = async () => {
  const { code } = await wx.login();
  const { data } = await request({ url: '/auth/wechat-login', method: 'POST', data: { code } });
  wx.setStorageSync('access_token', data.access_token);
  wx.setStorageSync('refresh_token', data.refresh_token);
  return data.user;
};

module.exports = { request, login };
```

要点：请求域名必须先在小程序后台登记白名单且为 HTTPS；401 统一走刷新重试；失败要给出可判断的错误结构。

## 2 微信支付 + 订阅消息（services/payment.js）

```javascript
const { request } = require('../utils/request');

const createOrder = async (orderData) => {
  // 1) 服务端下单，返回预付参数（签名必须在服务端完成）
  const prepayResult = await request({
    url: '/orders/create',
    method: 'POST',
    data: { items: orderData.items, address_id: orderData.addressId, coupon_id: orderData.couponId },
  });

  // 2) 调起支付
  return new Promise((resolve, reject) => {
    wx.requestPayment({
      timeStamp: prepayResult.timeStamp,
      nonceStr: prepayResult.nonceStr,
      package: prepayResult.package,     // prepay_id 形式
      signType: prepayResult.signType,   // RSA 或 MD5
      paySign: prepayResult.paySign,
      success: (res) => resolve({ success: true, orderId: prepayResult.orderId }),
      fail: (err) => {
        // 用户取消不算失败，单独分支处理
        if (err.errMsg.includes('cancel')) resolve({ success: false, reason: 'cancelled' });
        else reject({ success: false, reason: 'payment_failed', detail: err });
      },
    });
  });
};

// 订阅消息授权（已取代模板消息）
const requestSubscription = async (templateIds) => {
  return new Promise((resolve) => {
    wx.requestSubscribeMessage({
      tmplIds: templateIds,
      success: (res) => resolve({ accepted: templateIds.filter((id) => res[id] === 'accept'), result: res }),
      fail: () => resolve({ accepted: [], result: {} }),
    });
  });
};

module.exports = { createOrder, requestSubscription };
```

要点：`paySign` 等敏感签名一律服务端生成，客户端只透传；订阅授权应在**用户下单后**立即请求，此时同意率最高。

## 3 性能优先的页面模板（pages/product/product.js）

```javascript
const { request } = require('../../utils/request');

Page({
  data: { product: null, loading: true, skuSelected: {} },

  onLoad(options) {
    const { id } = options;
    this.productId = id;
    this.loadProduct(id);
    if (options.from === 'list') this.preloadRelatedProducts(id); // 预取下一页数据
  },

  async loadProduct(id) {
    try {
      const product = await request({ url: `/products/${id}` });
      // setData 只传视图需要的字段，控制跨线程数据量
      this.setData({
        product: {
          id: product.id, title: product.title, price: product.price,
          images: product.images.slice(0, 5), // 首屏只给 5 张
          skus: product.skus, description: product.description,
        },
        loading: false,
      });
      // 其余图片延迟补齐
      if (product.images.length > 5) {
        setTimeout(() => this.setData({ 'product.images': product.images }), 500);
      }
    } catch (err) {
      wx.showToast({ title: '加载失败', icon: 'none' });
      this.setData({ loading: false });
    }
  },

  onShareAppMessage() {
    const { product } = this.data;
    return {
      title: product?.title || '看看这个商品',
      path: `/pages/product/product?id=${this.productId}`,
      imageUrl: product?.images?.[0] || '',
    };
  },

  onShareTimeline() {
    const { product } = this.data;
    return { title: product?.title || '', query: `id=${this.productId}`, imageUrl: product?.images?.[0] || '' };
  },
});
```

要点：`setData` 每次都跨越 JS↔原生桥，合并更新、只传必要字段；首屏图片限量后延迟补齐；分享路径带参数以便转化追踪。
