document.addEventListener('DOMContentLoaded', () => {
    const sparklines = document.querySelectorAll('.sparkline');
    
    for (const canvas of sparklines) {
        const values = JSON.parse(canvas.dataset.values);
        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;
        
        // Clear canvas
        ctx.clearRect(0, 0, width, height);
        
        // Set up the path
        ctx.beginPath();
        ctx.strokeStyle = '#0052cc';
        ctx.lineWidth = 2;
        
        // Calculate points
        const max = Math.max(...values);
        const min = Math.min(...values);
        const range = max - min;
        
        values.forEach((value, index) => {
            const x = (index / (values.length - 1)) * width;
            const y = height - ((value - min) / range) * height;
            
            if (index === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        });
        
        // Draw the line
        ctx.stroke();
    }
}); 