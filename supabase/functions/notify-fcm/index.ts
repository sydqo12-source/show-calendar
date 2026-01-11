// supabase/functions/notify-fcm/index.ts

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from "https://esm.sh/@supabase/supabase-js@2"
// 구글 인증을 위한 공식 라이브러리 (V1 필수)
import { JWT } from "npm:google-auth-library@9"

interface EventRecord {
  id: number;
  title: string;
  [key: string]: any;
}

serve(async (req: Request) => {
  try {
    const payload = await req.json()
    const newEvent: EventRecord = payload.record 

    console.log(`🎤 새 이벤트 감지: ${newEvent.title}`)

    // 1. Supabase 연결
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    // 2. 알림 대상 토큰 찾기 (RPC)
    const { data: tokens, error } = await supabase
      .rpc('get_tokens_for_event', { 
        title_input: newEvent.title 
      })

    if (error) {
      console.error('토큰 조회 실패:', error)
      return new Response(JSON.stringify({ error: error.message }), { status: 500 })
    }

    if (!tokens || tokens.length === 0) {
      console.log('매칭되는 키워드 없음')
      return new Response('알림 대상 없음', { status: 200 })
    }

    // 3. Firebase V1 인증 토큰 생성 (핵심!)
    const serviceAccountStr = Deno.env.get('FIREBASE_SERVICE_ACCOUNT')
    if (!serviceAccountStr) {
      throw new Error('서비스 계정 키가 설정되지 않았습니다.')
    }
    
    const serviceAccount = JSON.parse(serviceAccountStr)
    
    const jwtClient = new JWT({
      email: serviceAccount.client_email,
      key: serviceAccount.private_key,
      scopes: ['https://www.googleapis.com/auth/firebase.messaging'],
    })
    
    const accessToken = await jwtClient.authorize()

    // 4. 알림 발송 (V1 방식)
    const projectId = serviceAccount.project_id
    
    const sendPromises = tokens.map((t: any) => {
      return fetch(`https://fcm.googleapis.com/v1/projects/${projectId}/messages:send`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken.access_token}` // 여기서 인증 토큰 사용
        },
        body: JSON.stringify({
          message: {
            token: t.fcm_token,
            notification: {
              title: '쇼콕! 키워드 알림 🎫',
              body: `'${newEvent.title}' 티켓팅 정보가 등록되었어요!`
            },
            data: {
              url: `https://showkok.com/events/${newEvent.id}`
            }
          }
        })
      })
    })

    await Promise.all(sendPromises)
    console.log(`${tokens.length}명에게 알림 전송 완료`)

    return new Response(
      JSON.stringify({ message: '전송 완료' }),
      { headers: { 'Content-Type': 'application/json' } }
    )

  } catch (err: any) {
    console.error(err)
    return new Response(JSON.stringify({ error: err.message }), { status: 400 })
  }
})