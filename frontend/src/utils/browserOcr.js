import { createWorker } from 'tesseract.js';
import * as pdfjsLib from 'pdfjs-dist';
import pdfWorkerUrl from 'pdfjs-dist/build/pdf.worker.min.mjs?url';

pdfjsLib.GlobalWorkerOptions.workerSrc = pdfWorkerUrl;

const MAX_PDF_PAGES = 30;
const OCR_MAX_WIDTH = 1600;

function clampScale(viewport) {
  if (viewport.width >= OCR_MAX_WIDTH) {
    return 1;
  }

  return OCR_MAX_WIDTH / viewport.width;
}

function canvasToBlob(canvas) {
  return new Promise((resolve, reject) => {
    canvas.toBlob(
      (blob) => {
        if (blob) {
          resolve(blob);
        } else {
          reject(
            new Error('Unable to create OCR image.'),
          );
        }
      },
      'image/png',
    );
  });
}

async function ocrImageSource(
  worker,
  source,
) {
  const result = await worker.recognize(source);

  return (result?.data?.text ?? '').trim();
}

async function extractPdfText(
  file,
  worker,
  onProgress,
) {
  const buffer = await file.arrayBuffer();

  const pdf = await pdfjsLib.getDocument({
    data: buffer,
    disableAutoFetch: true,
  }).promise;

  const totalPages = Math.min(
    pdf.numPages,
    MAX_PDF_PAGES,
  );

  const pages = [];

  for (let pageNumber = 1; pageNumber <= totalPages; pageNumber += 1) {
    const page = await pdf.getPage(pageNumber);

    try {
      // First try native PDF text extraction.
      const textContent =
        await page.getTextContent();

      const nativeText = textContent.items
        .map((item) =>
          typeof item.str === 'string'
            ? item.str
            : '',
        )
        .join(' ')
        .replace(/\s+/g, ' ')
        .trim();

      if (nativeText.length >= 20) {
        pages.push({
          page: pageNumber,
          text: nativeText,
        });
      } else {
        // Scanned/image-only page: OCR it in the browser.
        const baseViewport =
          page.getViewport({
            scale: 1,
          });

        const scale = Math.min(
          2,
          clampScale(baseViewport),
        );

        const viewport =
          page.getViewport({
            scale,
          });

        const canvas =
          document.createElement('canvas');

        const context =
          canvas.getContext('2d', {
            willReadFrequently: true,
          });

        canvas.width = Math.floor(
          viewport.width,
        );
        canvas.height = Math.floor(
          viewport.height,
        );

        await page.render({
          canvasContext: context,
          viewport,
        }).promise;

        const blob =
          await canvasToBlob(canvas);

        const text =
          await ocrImageSource(
            worker,
            blob,
          );

        if (text) {
          pages.push({
            page: pageNumber,
            text,
          });
        }

        canvas.width = 1;
        canvas.height = 1;
      }
    } finally {
      page.cleanup();
    }

    if (typeof onProgress === 'function') {
      const percentage =
        10 +
        Math.round(
          (pageNumber / totalPages) * 75,
        );

      onProgress(percentage);
    }
  }

  return pages;
}

async function extractImageText(
  file,
  worker,
  onProgress,
) {
  const text =
    await ocrImageSource(
      worker,
      file,
    );

  if (typeof onProgress === 'function') {
    onProgress(85);
  }

  return text
    ? [
        {
          page: 1,
          text,
        },
      ]
    : [];
}

export async function extractBrowserText(
  file,
  { onProgress } = {},
) {
  if (!file) {
    throw new Error(
      'No file was selected.',
    );
  }

  if (typeof onProgress === 'function') {
    onProgress(5);
  }

  const worker =
    await createWorker(
      'eng',
      1,
      {
        logger: (message) => {
          if (
            typeof onProgress !==
            'function'
          ) {
            return;
          }

          if (
            message.status ===
            'recognizing text'
          ) {
            const progress =
              Number(message.progress) ||
              0;

            onProgress(
              Math.min(
                85,
                10 +
                  Math.round(
                    progress * 70,
                  ),
              ),
            );
          }
        },
      },
    );

  try {
    const filename =
      file.name.toLowerCase();

    const isPdf =
      file.type === 'application/pdf' ||
      filename.endsWith('.pdf');

    const isImage =
      file.type.startsWith('image/') ||
      /\.(png|jpe?g|webp)$/i.test(
        filename,
      );

    if (isPdf) {
      return await extractPdfText(
        file,
        worker,
        onProgress,
      );
    }

    if (isImage) {
      return await extractImageText(
        file,
        worker,
        onProgress,
      );
    }

    throw new Error(
      'Unsupported file type.',
    );
  } finally {
    await worker.terminate();

    if (typeof onProgress === 'function') {
      onProgress(90);
    }
  }
}