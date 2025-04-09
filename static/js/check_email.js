document.addEventListener('DOMContentLoaded', function() {
    const shark = document.querySelector('.shark');

    function setRandomSharkPosition() {
        // Случайные координаты с учётом размеров акулы
        const randomX = Math.random() * (window.innerWidth - 200);
        const randomY = Math.random() * (window.innerHeight - 100);

        // Случайная длительность анимации (5–10 секунд)
        const randomDuration = Math.random() * 5 + 5;

        // Случайное направление (вправо или влево)
        const direction = Math.random() > 0.5 ? 1 : -1;
        const startX = direction === 1 ? -200 : window.innerWidth + 200;
        const endX = direction === 1 ? window.innerWidth + 200 : -200;

        // Устанавливаем начальную позицию
        shark.style.left = startX + 'px';
        shark.style.top = randomY + 'px';
        shark.style.transition = `left ${randomDuration}s linear`;

        // Переворачиваем акулу в зависимости от направления
        shark.style.transform = direction === 1 ? 'scaleX(1)' : 'scaleX(-1)';

        // Запускаем движение
        setTimeout(() => {
            shark.style.left = endX + 'px';
        }, 10);

        // Повторяем через случайный интервал
        setTimeout(setRandomSharkPosition, randomDuration * 1000);
    }

    // Запускаем анимацию
    setRandomSharkPosition();
});