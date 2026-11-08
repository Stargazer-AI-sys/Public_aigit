import { Hero } from "@/components/home/hero";
import { WorkingStyle } from "@/components/home/working-style";
import { Workflows } from "@/components/home/workflows";

// 각 섹션 컴포넌트가 자신의 section id(home, how, projects)를 직접 렌더링한다.
// 여기서 id를 다시 붙이면 중복 id가 생기므로 순서만 정한다.
export default function Home() {
  return (
    <>
      <Hero />
      <WorkingStyle />
      <Workflows />
    </>
  );
}
