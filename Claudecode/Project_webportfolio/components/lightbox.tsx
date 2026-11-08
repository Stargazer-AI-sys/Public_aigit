"use client";

import { useEffect, useRef, useState } from "react";

type LightboxProps = {
  open: boolean;
  onClose: () => void;
  src: string;
  alt: string;
  caption?: string;
};

// 목업 dialog.lightbox를 옮긴 것. 바깥(배경)이나 닫기 버튼을 누르거나 Esc로 닫는다.
export function Lightbox({ open, onClose, src, alt, caption }: LightboxProps) {
  const ref = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);

  return (
    <dialog
      ref={ref}
      aria-label="이미지 크게 보기"
      onClick={(e) => {
        // dialog 자체가 클릭 대상이면 ::backdrop(배경)을 누른 것이다.
        if (e.target === e.currentTarget) e.currentTarget.close();
      }}
      onClose={onClose}
      className="m-auto max-h-[94vh] max-w-[94vw] overflow-visible border-0 bg-transparent p-0 backdrop:bg-[rgba(8,12,20,.8)]"
    >
      {open && (
        <>
          <button
            type="button"
            aria-label="닫기"
            onClick={() => ref.current?.close()}
            className="absolute right-2 top-2 flex size-9 cursor-pointer items-center justify-center rounded-full border-0 bg-white text-[20px] leading-none text-[#111] shadow-[0_6px_18px_rgba(0,0,0,.3)] sm:-right-4 sm:-top-4"
          >
            ×
          </button>
          {/* 팝업 이미지는 원본 크기를 미리 알 수 없어 next/image 대신 img를 쓴다. */}
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={src}
            alt={alt}
            className="block h-auto max-h-[86vh] w-auto max-w-[94vw] rounded-xl shadow-[0_24px_60px_rgba(0,0,0,.45)]"
          />
          {caption ? (
            <p className="mx-auto mt-3 max-w-[90ch] text-center text-[13.5px] text-[#e6ebf3]">
              {caption}
            </p>
          ) : null}
        </>
      )}
    </dialog>
  );
}

type ZoomImageProps = {
  src: string;
  alt: string;
  /** 팝업 아래에 보일 캡션. 없으면 alt를 쓴다. */
  caption?: string;
  className?: string;
  /** 썸네일. 없으면 src 이미지를 그대로 보여준다. */
  children?: React.ReactNode;
};

// 감싼 내용을 누르면 src 이미지를 가운데 팝업으로 연다.
export function ZoomImage({ src, alt, caption, className, children }: ZoomImageProps) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <a
        href={src}
        className={className}
        onClick={(e) => {
          e.preventDefault();
          setOpen(true);
        }}
      >
        {children ?? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={src} alt={alt} />
        )}
      </a>
      <Lightbox
        open={open}
        onClose={() => setOpen(false)}
        src={src}
        alt={alt}
        caption={caption ?? alt}
      />
    </>
  );
}
