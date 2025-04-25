const fs = require('fs');
const path = require('path');

// 创建数据目录
const dataDir = path.join(__dirname, 'data');
if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir);
}

// 生成随机GPS坐标（基于北京中心点）
function generateCoordinate(baseLng, baseLat, range = 0.2) {
    return [
        baseLng + (Math.random() - 0.5) * range,
        baseLat + (Math.random() - 0.5) * (range * 0.75)
    ];
}

// 生成车辆数据
function generateVehicleData(numVehicles = 20) {
    const basePoint = [116.397428, 39.90923]; // 北京市中心
    const vehicles = [];
    
    for (let i = 0; i < numVehicles; i++) {
        const [longitude, latitude] = generateCoordinate(basePoint[0], basePoint[1]);
        vehicles.push({
            vehicle_id: `京A${Math.random().toString().substr(2,6)}`,
            longitude: longitude.toFixed(6),
            latitude: latitude.toFixed(6),
            status: Math.random() > 0.1 ? 'online' : 'offline',
            speed: (Math.random() * 80).toFixed(1),  // 新增速度
            direction: Math.floor(Math.random() * 360),  // 新增方向
            timestamp: new Date().toISOString()
        });
    }
    return vehicles;
}

// 生成CSV文件
function generateCSV(data) {
    const csvHeader = 'vehicle_id,longitude,latitude,status,timestamp\n';
    const csvContent = data.map(v => 
        `${v.vehicle_id},${v.longitude},${v.latitude},${v.status},${v.timestamp}`
    ).join('\n');
    
    fs.writeFileSync(path.join(dataDir, 'gps_data.csv'), csvHeader + csvContent);
}

// 生成JSON文件
function generateJSON(data) {
    fs.writeFileSync(
        path.join(dataDir, 'gps_data.json'),
        JSON.stringify({ vehicles: data }, null, 2)
    );
}

// 执行生成
const vehicleData = generateVehicleData();
generateCSV(vehicleData);
generateJSON(vehicleData);
console.log('GPS数据已生成至 /data 目录');