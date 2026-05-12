/**
 * 前端密码加密工具
 * 使用 Web Crypto API 对密码进行 SHA-256 哈希
 * 确保密码不以明文形式在网络中传输
 */

/**
 * 将密码进行 SHA-256 哈希
 * @param {string} password - 原始密码
 * @returns {Promise<string>} - 返回十六进制哈希字符串
 */
export async function hashPassword(password) {
  const encoder = new TextEncoder()
  const data = encoder.encode(password)
  const hashBuffer = await crypto.subtle.digest('SHA-256', data)
  const hashArray = Array.from(new Uint8Array(hashBuffer))
  const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('')
  return hashHex
}
