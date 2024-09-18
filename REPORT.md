# **Отчет по лабораторной работе omp1**
## Мхитарян Давид. Техническое Зрение

Цель работы — знакомство с расширением OpenMP для языков C/C++ для многопоточного программирования.

Само же задание состоит в том, чтобы растянуть гистограмму для цветового(-ых) канала(-ов) изображения и получить улучшенную контрастность.

## Описание работы алгоритма

1. Реализация алгоритма для формата P5 (полутоновое изображение, 1 канал цвета)

    1.1 Объявляем и сразу же инициализируем нулями статический массив-гистограмму. Проходимся по изображению и заполняем массив реальными значениями.

    ```c
    int histogram[256] = { 0 };
    for (int i = 0; i < imageSize; ++i) {
				histogram[pixels[i]]++;
    }
    ```

    1.2 Находим крайние ненулевые числа в "левой" и "правой" частях гистограммы, называем их min и max соответственно. В случае, если работаем с коэффициентом alpha, то отбрасываем alpha % пикселей с "левой" и "правой" частей и аналогично находим первые ненулевые значения.

    1.3 С помощью формулы для растяжения гистограммы проходим по изображению и для каждого пикселя рассчитываем новое значение. При этом в случае, когда min = max, гистограмму не растягиваем, так как возникнет деление на ноль. На выходе имеем измененный массив пикселей с улучшенной контрастностью.
   
    $y = (x - min)*255/(max - min)$
   

    ```c
    if (minVal != maxVal) {
        for (int i = 0; i < imageSize; ++i) {
            int newValue = static_cast<int>((pixels[i] - minVal) * (maxIntensity / static_cast<float>(maxVal - minVal)));
            pixels[i] = static_cast<unsigned char>(clamp(newValue, 0, maxIntensity));
        }
    }
    ```

2. Реализация алгоритма для формата P5 с применением OpenMP

    2.1 Объявляем и сразу же инициализируем нулями статический массив-гистограмму.

    2.2 С помощью директивы *#pragma omp parallel num_threads(ompThreads)* объявляем участок кода с параллельными вычислениями, при этом число потоков = ompThreads, заданному во входных параметрах. В нем для каждого потока создается и заполняется нулями массив - локальная гистограмма.

    ```c
    #pragma omp parallel num_threads(ompThreads) 
    {
				int localHistogram[256] = { 0 };
				#pragma omp for schedule(dynamic, 16384)
				for (int i = 0; i < imageSize; ++i) {
					localHistogram[pixels[i]]++;
				}

				#pragma omp critical
				for (int i = 0; i < 256; ++i)
				{
					histogram[i] += localHistogram[i];
				}
    }
    ```

    2.3 Директива *#pragma omp for schedule(dynamic, 16384)* указывает, что следующий цикл for будет распараллелен, при этом итерации между потоками будут распределяться динамически с размером блока в 16384 итерации (или меньше, если осталось меньше итераций). Преимущество dynamic над static в том, что static заранее знает, что определенный тред будет выполнять определенную итерацию, из-за чего при достаточно большом размере imageSize некоторые треды быстрее успеют выполнить свою итерацию и будут ждать остальных. В то время, как dynamic будет по ситуации определять свободные треды. Размер чанка 16384 был выбран эмпирически.
    
    Выход из цикла for будет одновременным для всех потоков, так как директива позволяет иметь в конце цикла неявный барьер, заставляющий ждать завершение работы цикла для остальных потоков.

    2.4 После того, как каждый поток посчитал свою гистограмму, необходимо получить итоговую. Директива #pragma omp critical позволяет по очереди выполнять цикл for для каждого потока, чтобы не допустить гонки данных.  Пока 1 поток полностью не выполнит цикл, другие будут его ждать. Каждая private-переменная складывается с общей shared-переменной histogram. На выходе после параллельного участка имеем гистограмму.

    2.5 Аналогично 1.2 находим минимум и максимум гистограммы. Здесь не используем параллелизм, так как цикл имеет очень малый размер, простое тело и выполняется очень быстро порядка 10^-6 сек.

    2.6 Для растяжения гистограммы объявляем параллельный регион, а в нем цикл for с динамическим распределением итераций с размером чанка 1024. Причина выбора dynamic аналогична 2.3. На выходе имеем измененный массив пикселей с улучшенной контрастностью.
    ```c
    #pragma omp parallel num_threads(ompThreads) 
    {
		#pragma omp for schedule(dynamic, 1024)
		for (int i = 0; i < imageSize; ++i) {
			int newValue = static_cast<int>((pixels[i] - minVal) * (maxIntensity / static_cast<float>(maxVal - minVal)));
			pixels[i] = static_cast<unsigned char>(clamp(newValue, 0, maxIntensity));
		}
    }
    ```

3. Реализация алгоритма для формата P6 (изображение с 3 каналами цвета RGB)

    3.1 Объявляем и сразу же инициализируем нулями 3 статических массива-гистограмм для каналов RGB. Проходимся по изображению и заполняем массивы реальными значениями.
    ```c
    for (int i = 0; i < imageSize; i += 3) {
				++histogramR[pixels[i]];
				++histogramG[pixels[i + 1]];
				++histogramB[pixels[i + 2]];
        }   
    ```

    3.2 Находим крайние ненулевые числа в "левой" и "правой" частях гистограммы аналогично 1.2, но только для трех гистограмм. Затем находим  минимум и максимум среди трех цветов.
    ```c
    unsigned char minR = 255, maxR = 0;
    unsigned char minG = 255, maxG = 0;
    unsigned char minB = 255, maxB = 0;
    int totalPixels = width * height;

    findMinMaxHist(histogramR, minR, maxR, alpha, totalPixels);
    findMinMaxHist(histogramG, minG, maxG, alpha, totalPixels);
    findMinMaxHist(histogramB, minB, maxB, alpha, totalPixels);

    int minVal = findMinRGB(minR, minG, minB);
    int maxVal = findMaxRGB(maxR, maxG, maxB);
    ```

    3.3 Растягиваем гистограммы аналогично 1.3, но делаем цикл с шагом i+=3, так как в массиве пикселей оттенки хранятся последовательно: r, g, b, r, g.. 
    ```c
    for (int i = 0; i < imageSize; i += 3) {
		int newR = static_cast<int>((pixels[i] - minR) * (maxIntensity / static_cast<float>(maxR - minR)));
		int newG = static_cast<int>((pixels[i + 1] - minG) * (maxIntensity / static_cast<float>(maxG - minG)));
		int newB = static_cast<int>((pixels[i + 2] - minB) * (maxIntensity / static_cast<float>(maxB - minB)));

		pixels[i] = static_cast<unsigned char>(clamp(newR, 0, maxIntensity));
		pixels[i + 1] = static_cast<unsigned char>(clamp(newG, 0, maxIntensity));
		pixels[i + 2] = static_cast<unsigned char>(clamp(newB, 0, maxIntensity));
    }
    ```

4. Реализация алгоритма для формата P6 с применением OpenMP

    4.1 Объявляем и сразу же инициализируем нулями 3 статических массива-гистограмм для каналов RGB.

    4.2 Создаем параллельную область и для каждого потока создаем 3 локальных переменных - гистограмм. Цикл выглядит аналогично 3.1, но с директивой динамического распределения итераций для цикла for #pragma omp for schedule(static, 16384). Объяснение аналогично 2.2, размер чанка подбирал эмпирически и решил оставить таким же.
    ```c
    #pragma omp parallel num_threads(ompThreads)
    {	
		int localHistogramR[256] = { 0 };
		int localHistogramG[256] = { 0 };
		int localHistogramB[256] = { 0 };

		#pragma omp for schedule(dynamic, 16384)
		for (int i = 0; i < imageSize; i += 3) {
			++localHistogramR[pixels[i]];
			++localHistogramG[pixels[i + 1]];
			++localHistogramB[pixels[i + 2]];
		}
				
		#pragma omp critical
		{
			for (int i = 0; i < 256; ++i)
			{
				histogramR[i] += localHistogramR[i];
				histogramG[i] += localHistogramG[i];
				histogramB[i] += localHistogramB[i];
			}
		}
    }
    ```

    4.3 Аналогично 2.3 заполняем глобальные гистограммы локальными поочередно из каждого потока.

    4.4 Находим минимум и максимум оттенка среди пикселей, как в 3.2. 

    4.5 Для растяжения гистограммы объявляем параллельный регион, а в нем цикл for с динамическим распределением итераций аналогично 2.6. Размер чанка оставил тем же.
    ```c
    #pragma omp parallel num_threads(ompThreads) 
    {
		#pragma omp for schedule(dynamic, 1024)
		for (int i = 0; i < imageSize; i += 3) {
			int newR = static_cast<int>((pixels[i] - minR) * (maxIntensity / static_cast<float>(maxR - minR)));
			int newG = static_cast<int>((pixels[i + 1] - minG) * (maxIntensity / static_cast<float>(maxG - minG)));
			int newB = static_cast<int>((pixels[i + 2] - minB) * (maxIntensity / static_cast<float>(maxB - minB)));

			pixels[i] = static_cast<unsigned char>(clamp(newR, 0, maxIntensity));
			pixels[i + 1] = static_cast<unsigned char>(clamp(newG, 0, maxIntensity));
			pixels[i + 2] = static_cast<unsigned char>(clamp(newB, 0, maxIntensity));
		}
    }
    ```

## Результаты

Замеры проводились на устройстве Win11 с процессором Intel Core i5 12450H с компилятором Visual C++.

1. Рассмотрим время работы программы с разным количеством потоков на основе трех изображений: лягушка (черно-белое, 458 КБ), лягушка (цветная, 1374 КБ), мост (цветной, 64801 КБ). Коэффициент alpha = 0. Время дано в секундах.

| ompThreads | Лягушка (ч/б) | Лягушка (цвет) | Мост      |
|------------|---------------|----------------|-----------|
| no-omp     | 0.0008135     | 0.0021264      | 0.116801  |
| 1          | 0.0008329     | 0.0020297      | 0.109421  |
| 2          | 0.0007607     | 0.0016881      | 0.0718936 |
| 4          | 0.0006851     | 0.0014052      | 0.0545512 |
| 8          | 0.0008706     | 0.0013491      | 0.0454272 |
| 12         | 0.0007722     | 0.0012413      | 0.0416127 |

---
![1](https://downloader.disk.yandex.ru/preview/45861ab65aad56e97bb8307b6d6e3419f761c4d00c7acbae42814b9177ac9937/66eb449b/7Bw1whCeKv2aRwPeq916jchDgexzNvGwavGg4GgHX08gBMtSK2kyf6uJnGSuNdzdtGlsORc6LE5Z60a8UT-xsw%3D%3D?uid=0&filename=gr.png&disposition=inline&hash=&limit=0&content_type=image%2Fpng&owner_uid=0&tknv=v2&size=2048x2048)
---
Можно заметить, что для изображений малых размеров многопоточность не играет сильной роли, так как тратится дополнительное время на выделение потоков и их закрытие. А в случае с мостом (63 МБ) параллелизм значительно ускоряет время работы программы. Особенно сильно выделяется сдвиг при переходе с однопоточного режима на двухпоточный. Выигрыш по времени при переходе с с однопоточного режима в многопоточный с 12 потоками около 2.5 раз.

2. Рассмотрим, как влияет chunkSize в работе параллельной программы с директивой schedule на примере цветного изображения моста, для этого сделаем единый размер чанков во всех циклах. Время дано в секундах, количество потоков: 12.

| chunkSize | dynamic   | static    |
|-----------|-----------|-----------|
| 1         | 0.836974  | 0.0954968 |
| 10        | 0.24238   | 0.0545504 |
| 50        | 0.0929621 | 0.0521887 |
| 100       | 0.0675216 | 0.0551034 |
| 200       | 0.0524429 | 0.0507393 |
| 500       | 0.0495453 | 0.0531784 |
| 1000      | 0.0474532 | 0.0464021 |
| 5000      | 0.0442575 | 0.0478594 |
| 10000     | 0.0400819 | 0.0457313 |
| 20000     | 0.0411283 | 0.0484611 |

![](https://downloader.disk.yandex.ru/preview/e75720190c6d5d9af8abc4d79ee61ebd609d56af099ebb2e28406c2f66bc83f1/66eb4d5d/B0TgN4Y8tgZEKyIXn_2UAmaeQuSWqZmb3j7dJwDZ-FWU6RxqM7VS6jw3FJ_lWMRZAaf3Cj3qXOXh928hWAMjfA%3D%3D?uid=0&filename=gr2.png&disposition=inline&hash=&limit=0&content_type=image%2Fpng&owner_uid=0&tknv=v2&size=2048x2048)
---
Теперь рассмотрим результаты.

На малых размерах чанка dynamic кратно медленнее static из-за частых запросов на новые чанки, что создает накладные расходы. С ростом размера чанка dynamic становится быстрее, так как лучше балансирует нагрузку между потоками. На больших размерах чанка dynamic и static выравниваются с дальнейшей относительно незначительной пользой dynamic.
