function toggleSidebar() {
    var sidebar = document.getElementById('sidebar');
    if (sidebar.classList.contains('collapsed')) {
        sidebar.classList.remove('collapsed');
        updateVideoFrameWidth(250);
    } else {
        sidebar.classList.add('collapsed');
        updateVideoFrameWidth(60);
    }
}

function updateVideoFrameWidth(sidebarWidth) {
    var videoFrame = document.getElementById('videoFrame');
    videoFrame.style.left = `${sidebarWidth}px`;
    videoFrame.style.width = `calc(100% - ${sidebarWidth}px)`;
}

function changeVideoSrc(newSrc) {
    document.getElementById('videoFrame').src = newSrc;
}
// 定义加载数据并生成链接的函数
async function fetchAndGenerateLinks(url) {
    try {
        // 从指定的URL获取数据
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Failed to fetch data from ${url}: ${response.statusText}`);
        }

        // 解析数据
        const data = await response.text();
        const rows = data.split('\n');

        let linksData = [];

        rows.forEach(row => {
            const columns = row.split('\t');
            if (columns.length === 2) {
                const [ip, description] = columns;
                linksData.push({
                    ip: ip.trim(),
                    description: description.trim()
                });
            }
        });

        // 对数据按照 description 进行排序
        linksData.sort((a, b) => {
            if (a.description < b.description) return -1;
            if (a.description > b.description) return 1;
            return 0;
        });

        const linksList = document.getElementById('linksList');
        linksList.innerHTML = ''; // 清空现有列表项

        linksData.forEach(item => {
            const linkText = item.description || item.ip; // 如果描述为空，则使用IP作为链接文本

            // 创建一个新的列表项
            const listItem = document.createElement('li');

            // 创建一个新的链接元素
            const link = document.createElement('a');
            link.href = `http://192.168.129.200:8889/proxy_${item.ip}/`;
            link.textContent = linkText;
            link.onclick = function(event) {
                event.preventDefault(); // 阻止默认行为
                changeVideoSrc(this.href);
            };

            // 将链接添加到列表项中
            listItem.appendChild(link);

            // 将列表项添加到DOM中
            linksList.appendChild(listItem);
        });

    } catch (error) {
        console.error('Error fetching or processing the data:', error);
    }
}


// 调用函数并传入数据URL
fetchAndGenerateLinks("cameras.txt");