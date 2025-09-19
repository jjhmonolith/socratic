from fastapi import APIRouter, HTTPException
from app.models.request_models import (
    TopicInputRequest, 
    SocraticChatRequest, 
    SocraticChatResponse,
    InitialMessageRequest,
    InitialMessageResponse
)
from app.services.socratic_service import SocraticService
from app.services.socratic_assessment_service import get_socratic_assessment_service
from app.services.database_service import get_database_service
from app.core.config import get_settings

router = APIRouter()

def get_socratic_service():
    return SocraticService()

def get_assessment_service():
    return get_socratic_assessment_service()

@router.post("/topic/validate", response_model=dict)
async def validate_topic(request: TopicInputRequest):
    """주제 입력 검증 및 산파법 프롬프트 구축"""
    try:
        socratic_service = get_socratic_service()
        is_valid = await socratic_service.validate_topic(request.topic_content)
        if not is_valid:
            raise HTTPException(status_code=400, detail="부적절한 학습 주제입니다.")
        
        return {"valid": True, "message": "학습 주제가 설정되었습니다."}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/initial", response_model=InitialMessageResponse)
async def get_initial_message(request: InitialMessageRequest):
    """첫 대화 메시지 생성"""
    try:
        socratic_service = get_socratic_service()
        initial_message = await socratic_service.generate_initial_message(request.topic)
        
        return InitialMessageResponse(
            initial_message=initial_message,
            understanding_score=0
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/socratic", response_model=SocraticChatResponse)
async def socratic_chat(request: SocraticChatRequest):
    """소크라테스식 대화 및 이해도 평가"""
    try:
        socratic_service = get_socratic_service()
        assessment_service = get_assessment_service()
        settings = get_settings()

        # 병렬로 산파법 응답과 이해도 평가 실행
        socratic_response = await socratic_service.generate_socratic_response(
            request.topic,
            request.messages,
            request.understanding_level
        )

        # 사용자의 마지막 메시지와 AI 응답으로 5차원 소크라테스식 평가
        last_user_message = request.messages[-1]["content"] if request.messages else ""
        evaluation_result = await assessment_service.evaluate_socratic_dimensions(
            request.topic,
            last_user_message,
            socratic_response,
            request.messages,  # 전체 대화 기록
            request.difficulty
        )

        understanding_score = evaluation_result["overall_score"]
        is_completed = evaluation_result["is_completed"]

        # 데이터베이스 점수 저장 (student_id와 session_id가 있는 경우)
        if settings.use_database and request.student_id and request.session_id:
            database_service = get_database_service()

            # 먼저 학생의 메시지를 저장하여 message_id 획득
            user_message_id = await database_service.save_message(
                session_id=request.session_id,
                student_id=request.student_id,
                content=last_user_message,
                message_type="user"
            )

            # AI 응답도 저장
            ai_message_id = await database_service.save_message(
                session_id=request.session_id,
                student_id=request.student_id,
                content=socratic_response,
                message_type="assistant"
            )

            if user_message_id and ai_message_id:
                # 점수 기록 저장 (사용자 메시지에 대한 평가)
                score_saved = await database_service.save_score_record(
                    session_id=request.session_id,
                    student_id=request.student_id,
                    message_id=user_message_id,
                    evaluation_result=evaluation_result
                )

                if score_saved:
                    print(f"✅ Score record saved for student {request.student_id}")
                else:
                    print(f"❌ Failed to save score record for student {request.student_id}")
            else:
                print(f"❌ Failed to save messages for student {request.student_id}")

        return SocraticChatResponse(
            socratic_response=socratic_response,
            understanding_score=understanding_score,
            is_completed=is_completed,
            dimensions=evaluation_result["dimensions"],
            insights=evaluation_result["insights"],
            growth_indicators=evaluation_result["growth_indicators"],
            next_focus=evaluation_result["next_focus"]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))